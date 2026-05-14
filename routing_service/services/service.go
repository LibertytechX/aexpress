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
	Table(ctx context.Context, origin, destinations string) (*types.OSRMTableResponse, error)
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
		log.Printf("Error sending request to OSRM (Directions): ❌%v", err)
		return nil, err
	}

	if response.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("OSRM returned non-OK status (Directions): %d", response.StatusCode)
	}

	var directionsResponse types.OSRMDirectionsResponse
	if err := json.NewDecoder(response.Body).Decode(&directionsResponse); err != nil {
		log.Printf("Error decoding OSRM response (Directions): ❌%v", err)
		return nil, err
	}

	return &directionsResponse, nil
}

func (s *osrmService) Table(ctx context.Context, origin, destinations string) (*types.OSRMTableResponse, error) {
	// url for table: /table/v1/{profile}/{coordinates}?sources={source_indices}&annotations=distance,duration
	// we assume the first coordinate in the semicolon separated string is the origin (source=0)
	url := fmt.Sprintf("%s/table/v1/driving/%s;%s?sources=0&annotations=distance,duration", s.osrmBaseUrl, origin, destinations)

	req := utils.NewRequest("GET", url, nil, nil, ctx)
	response, err := req.Send()
	if err != nil {
		log.Printf("Error sending request to OSRM (Table): ❌%v", err)
		return nil, err
	}

	if response.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("OSRM returned non-OK status (Table): %d", response.StatusCode)
	}

	var tableResponse types.OSRMTableResponse
	if err := json.NewDecoder(response.Body).Decode(&tableResponse); err != nil {
		log.Printf("Error decoding OSRM response (Table): ❌%v", err)
		return nil, err
	}

	return &tableResponse, nil
}

