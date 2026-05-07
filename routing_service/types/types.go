package types

type OSRMDirectionsResponse struct {
	Code      string     `json:"code"`
	Routes    []Route    `json:"routes"`
	Waypoints []Waypoint `json:"waypoints"`
}

type Route struct {
	Geometry   string  `json:"geometry"`
	Legs       []Leg   `json:"legs"`
	Distance   float64 `json:"distance"`
	Duration   float64 `json:"duration"`
	WeightName string  `json:"weight_name"`
	Weight     float64 `json:"weight"`
}

type Leg struct {
	Steps    []Step  `json:"steps"`
	Distance float64 `json:"distance"`
	Duration float64 `json:"duration"`
	Summary  string  `json:"summary"`
	Weight   float64 `json:"weight"`
}

type Step struct {
	// Add step fields if needed later, currently empty in provided JSON
}

type Waypoint struct {
	Hint     string    `json:"hint"`
	Distance float64   `json:"distance"`
	Name     string    `json:"name"`
	Location []float64 `json:"location"`
}

type Coordinate struct {
	Lat float64 `json:"lat"`
	Lng float64 `json:"lng"`
}

type DirectionsRequest struct {
	Origin       Coordinate   `json:"origin"`
	Destinations []Coordinate `json:"destinations"`
}
