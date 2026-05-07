package utils

import "log"

// Response is a utility function that generates a standard response format for restful APIs.
// It takes a status code, data, and message as input parameters.
// It returns a map containing the status, data, message, and status code.
func Response(statusCode int, data any, message any) map[string]any {
	var status string
	switch {
	case statusCode >= 200 && statusCode <= 299:
		status = "success"
	case statusCode == 400:
		status = "error"
	case statusCode >= 300 && statusCode <= 399:
		status = "redirect"
	case statusCode == 404:
		status = "not found"
	case statusCode >= 405 && statusCode <= 499:
		status = "error"
	case statusCode == 401 || statusCode == 403:
		status = "unauthorized"
	case statusCode >= 500:
		status = "error"
		message = "This is from us!, please contact admin"
	default:
		status = "error"
		message = "This is from us!, please contact admin"
	}
	res := map[string]any{
		"status":      status,
		"data":        data,
		"message":     message,
		"status_code": statusCode,
	}
	return res

}

func HandleError(err error) {
	if err != nil {
		// log error
		log.Println(err)
	}
}
