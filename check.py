class QuizComments(BaseModel):
    session_id = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(User, related_name="quiz_comments", on_delete=models.CASCADE, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Quiz Comment"
        verbose_name_plural = "Quiz Comments"
        
class PublishQuizComments(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        user = request.user
        print(f"SESSIION ID >>> {session_id}")
        logs.info("entering QUIZ COMMENTS API ::::::: ")

        try:
            int(session_id)
            logs.info(f"exiting QUIZ COMMENTS API << Invalid session id, must be an integer>> ")
        except ValueError:
            return Response({
                "status": "failed",
                "message": "Invalid session id, must be an integer"
            }, status=400)

        serializer = QuizCommentsSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.validated_data.get("comment")
            
            try:
                session = LiveQuizSession.objects.get(id=session_id)
            except LiveQuizSession.DoesNotExist:
                data = {
                    "status": "failed",
                    "message": f"Session with id `{session_id}` does not exist",
                }
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            if session.status == StatusChoices.COMPLETED:
                data = {
                    "status": "failed",
                    "message": "Cannot post comment for a completed session.",
                }
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            comment = QuizComments.objects.create(
                session_id=session_id,
                user=user,
                comment=comment,
                is_published=True,
            )
            
            comment_event = {
                "quiz_id": session.id,
                "user_id": user.id,
                "user_name": user.get_user_fullname(),
                "user_phone": user.phone_number,
                "comment": comment.comment,
                "comment_id": comment.id
            }
            
            ably_pub_instance.publish(
                name="publish-comment",
                channel_name=f"publish/comment/{session_id}",
                data=comment_event
            )

            # mqtt_instance.publish(topic=settings.MQTT_TOPIC, payload=json.dumps(comment_event))

            logs.info(f"PUBLISH QUIZ COMMENTS PUBLISHING COMMENTS >> {comment_event}")

            logs.info(f"exiting QUIZ COMMENTS API << SUCCESSFUL >> ")
            
            data = {"status": "success", "message": "Comment processed succesfully."}
            return Response(data, status=status.HTTP_200_OK)

        else:
            data = {
                "status": "failed",
                "message": get_serializer_key_error(serializer.errors),
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
        
class AblyRestPublisher:
    """
    Backend-safe Ably publisher using the REST SDK.

    This class is intentionally limited to:
    - Publishing messages
    - Multi-channel publishing
    - Idempotent publishing
    - Channel access

    It DOES NOT:
    - Open realtime connections
    - Subscribe to channels
    - Manage presence
    - Attach or detach channels

    This design ensures:
    - Statelessness
    - Horizontal scalability
    - Safe usage inside HTTP requests and background jobs
    """

    def _init_(self, api_key: str):
        """
        Initialize the Ably REST client.

        Args:
            api_key (str):
                Ably API key with publish capability.
                This key must NEVER be exposed to the frontend.
        """
        self.ably = AblyRestSync(key=api_key)
    # ---------------------------------------------------------
    # CHANNEL ACCESS
    # ---------------------------------------------------------

    def get_channel(self, channel_name: str):
        """
        Get a reference to an Ably channel.

        Important:
        - Channels in Ably are created implicitly.
        - Calling this does NOT create network traffic.
        - The channel becomes active only when publishing occurs.

        Args:
            channel_name (str):
                The name of the channel.

        Returns:
            Channel:
                An Ably channel instance.
        """
        return self.ably.channels.get(channel_name)

    # ---------------------------------------------------------
    # PUBLISHING
    # ---------------------------------------------------------

    def publish(
        self,
        channel_name: str,
        name: str,
        data,
    ):
        """
        Publish a single message to a channel.

        This is the most common backend operation.

        Characteristics:
        - Stateless
        - Safe for retries
        - Suitable for HTTP views and workers

        Args:
            channel_name (str):
                Target channel.
            name (str):
                Message name (event type).
            data (Any):
                Serializable payload (dict, list, string, etc.).
        """
        channel = self.get_channel(channel_name)
        response = channel.publish(name, data)
        print("STATUS CODE:", response.status_code)
        # print("SUCCESS:", response.is_success())
        print("TEXT:", response.text)
            

    def publish_idempotent(
        self,
        channel_name: str,
        name: str,
        data,
        message_id: str = None,
    ):
        """
        Publish an idempotent message to a channel.

        Idempotent publishing ensures that:
        - Retried requests do NOT create duplicate messages
        - Ably de-duplicates messages with the same ID

        Best practice:
        - Use a stable ID derived from your business logic
        - Or let the method generate one

        Args:
            channel_name (str):
                Target channel.
            name (str):
                Message name.
            data (Any):
                Message payload.
            message_id (str | None):
                Optional unique message ID.
                If not provided, a UUID is generated.
        """
        channel = self.get_channel(channel_name)

        message = Message(
            name=name,
            data=data,
            id=message_id or str(uuid.uuid4()),
        )

        channel.publish(message)

    def publish_multiple(
        self,
        channel_names: list[str],
        name: str,
        data,
        *,
        idempotent: bool = False,
    ):
        """
        Publish the same message to multiple channels.

        Use cases:
        - Fan-out notifications
        - Broadcasting system events
        - Multi-user updates

        Notes:
        - This method publishes sequentially.
        - If idempotent=True, each channel gets a unique message ID.
        - For atomic batch publishing, Ably batch APIs may be used.

        Args:
            channel_names (list[str]):
                List of channel names.
            name (str):
                Message name.
            data (Any):
                Message payload.
            idempotent (bool):
                Whether to enable idempotent publishing.
        """
        for channel_name in channel_names:
            if idempotent:
                self.publish_idempotent(
                    channel_name=channel_name,
                    name=name,
                    data=data,
                )
            else:
                self.publish(
                    channel_name=channel_name,
                    name=name,
                    data=data,
                )