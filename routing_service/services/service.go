package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"routing_service/types"
	"routing_service/utils"
)

// service layer is where the business logic of the application resides.

type RoutingService interface {
	Directions(ctx context.Context, origin, destination string) (*types.OSRMDirectionsResponse, error)
}

type osrmService struct {
	osrmBaseUrl string
}

func NewRoutingService(osrmBaseUrl string) RoutingService {
	return &osrmService{osrmBaseUrl: osrmBaseUrl}
}

func (s *osrmService) Directions(ctx context.Context, origin, destination string) (*types.OSRMDirectionsResponse, error) {
	url := fmt.Sprintf("%s/route/v1/driving/%s;%s?annotations=duration,distance", s.osrmBaseUrl, origin, destination)

	req := utils.NewRequest("GET", url, nil, nil, ctx)
	response, err := req.Send()
	if err != nil {
		log.Printf("Error sending request to OSRM: ❌%v", err)
		return nil, err
	}

	if response.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("OSRM returned non-OK status: %d", response.StatusCode)
	}

	var directionsResponse types.OSRMDirectionsResponse
	if err := json.NewDecoder(response.Body).Decode(&directionsResponse); err != nil {
		log.Printf("Error decoding OSRM response: ❌%v", err)
		return nil, err
	}

	return &directionsResponse, nil
}
