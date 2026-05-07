package service

import "context"

// service layer is where the business logic of the application resides.

type RoutingService interface {
	Directions(ctx context.Context, origin, destination []float64) (float64, float64, error)
}
