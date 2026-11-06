package controller

import (
	"context"
	"log"
	"net/http"
	"routing_service/middleware"
	service "routing_service/services"
	"routing_service/utils"
	"strings"

	"github.com/gin-gonic/gin"
)

type Controller struct {
	// depend on services
	service service.RoutingService
}

func NewController(routingService service.RoutingService) *Controller {
	return &Controller{
		service: routingService,
	}
}

// register routes
func (c *Controller) RegisterRoutes(router *gin.RouterGroup) {
	router.GET("/directions", middleware.AuthMiddleware(), c.GetDirections)
	router.GET("/table", middleware.AuthMiddleware(), c.GetTable)
}

func (c *Controller) GetDirections(ctx *gin.Context) {
	log.Println("Received request for directions 🚗🚗")
	// get the query params for origin and destinations
	origin := ctx.Query("origin")
	destinations := ctx.QueryArray("destinations")
	log.Println("Origin:", origin)
	log.Println("Destinations:", destinations)
	if origin == "" || len(destinations) == 0 {
		ctx.JSON(http.StatusBadRequest, utils.Response(http.StatusBadRequest, nil, "Origin and destinations are required"))
		return
	}

	// shadow the destinations from list to string
	destinationsStr := strings.Join(destinations, ";")
	log.Println("Destinations (updated):", destinationsStr)
	bgCtx := context.Background()
	// send to service layer to process
	response, err := c.service.Directions(bgCtx, origin, destinationsStr)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, utils.Response(http.StatusInternalServerError, nil, "Failed to get directions"))
		return
	}
	routeData := response.Routes

	ctx.JSON(http.StatusOK, utils.Response(http.StatusOK, routeData, "Directions fetched successfully 🔥🔥"))
}

func (c *Controller) GetTable(ctx *gin.Context) {
	log.Println("Received request for table (distance matrix) 📊📊")
	origin := ctx.Query("origin")
	destinations := ctx.QueryArray("destinations")
	log.Println("Origin:", origin)
	log.Println("Destinations:", destinations)
	if origin == "" || len(destinations) == 0 {
		ctx.JSON(http.StatusBadRequest, utils.Response(http.StatusBadRequest, nil, "Origin and destinations are required"))
		return
	}

	destinationsStr := strings.Join(destinations, ";")
	bgCtx := context.Background()
	response, err := c.service.Table(bgCtx, origin, destinationsStr)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, utils.Response(http.StatusInternalServerError, nil, "Failed to get distance table"))
		return
	}

	ctx.JSON(http.StatusOK, utils.Response(http.StatusOK, response, "Distance table fetched successfully 🔥🔥"))
}

