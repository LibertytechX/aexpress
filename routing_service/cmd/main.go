package main

import (
	"log"
	"net/http"
	"os"
	"routing_service/utils"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func init() {
	// Load .env file if it exists
	godotenv.Load()
}

func main() {
	// Get OSRM URL from env var or use default
	osrmURL := os.Getenv("OSRM_URL")
	if osrmURL == "" {
		osrmURL = "http://localhost:5001"
	}
	log.Println("OSRM URL: ", osrmURL)
	log.Println("Starting server...🔥🔥")
	// get the env var for the addr
	addr := os.Getenv("ADDR")
	if addr == "" {
		addr = ":8081"
	}
	// let's set up gin
	router := gin.Default()
	router.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"},
		AllowMethods:     []string{"GET", "POST"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization", "Proctor-Env"},
		AllowCredentials: true,
	}))

	// setup health check route
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, utils.Response(http.StatusOK, gin.H{"status": "ok"}, nil))
	})
	router.GET("/", func(ctx *gin.Context) {
		ctx.JSON(http.StatusOK, gin.H{
			"message": "Welcome to the Assured Express Routing Service API",
			"endpoints": gin.H{
				"health": "/health",
			},
		})
	})

	if err := router.Run(addr); err != nil {
		log.Fatal("Server failed to start ❌❌: ", err)
	}

	log.Println("🚀🚀 Server running on 🚀🚀", addr)

	// Implement routing logic here...
}
