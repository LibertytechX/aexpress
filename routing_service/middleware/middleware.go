package middleware

import (
	"net/http"
	"os"
	"routing_service/utils"

	"github.com/gin-gonic/gin"
)

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		apiKey := c.GetHeader("X-API-Key")
		expectedKey := os.Getenv("API_KEY")

		if apiKey == "" || apiKey != expectedKey {
			c.JSON(http.StatusUnauthorized, utils.Response(http.StatusUnauthorized, nil, "Unauthorized: Invalid or missing API Key"))
			c.Abort()
			return
		}
		c.Next()
	}
}
