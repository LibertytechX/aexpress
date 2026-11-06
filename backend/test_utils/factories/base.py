from factory.django import DjangoModelFactory


class LibertyBaseFactory(DjangoModelFactory):
    """
    Parent factory for all Liberty model factories.

    Conventions:
    - skip_postgeneration_save=True prevents the double-save that triggers
      signals twice when PostGenerationMethodCall (e.g. set_password) is used.
    - All app-level factories should extend this class.
    """

    class Meta:
        abstract = True
        skip_postgeneration_save = True
