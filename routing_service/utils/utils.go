package utils

import (
	"bytes"
	"context"
	"encoding/json"
	"log"
	"net/http"
	"strings"
)

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

// Request struct represents an HTTP request to be sent to the Azure OpenAI API
type Request struct {
	ctx     context.Context
	body    any
	method  string
	url     string
	headers map[string]interface{}
}

// It contains the request body, method, URL, and headers.
// The body can be of any type, and the headers are a map of string keys to interface{} values.
// The method is the HTTP method (e.g., GET, POST) to be used for the request.
// The URL is the endpoint of the Azure OpenAI API to which the request will be sent.
// The headers are optional and can be used to set any additional headers required by the API.
func NewRequest(method string, url string, body any, headers map[string]interface{}, ctx context.Context) *Request {
	return &Request{
		body:    body,
		method:  method,
		url:     url,
		headers: headers,
		ctx:     ctx,
	}
}

// The Request struct is used to create and send requests to the Azure OpenAI API.
// It has a method Send() that sends the request and returns the response.
func (r *Request) Send() (*http.Response, error) {
	data, err := json.Marshal(r.body)
	if err != nil {
		log.Printf("Error marshalling request body: %v", err)
		return nil, err
	}
	client := &http.Client{}
	method := strings.ToUpper(r.method)
	req, err := http.NewRequestWithContext(r.ctx, method, r.url, bytes.NewBuffer(data))
	if err != nil {
		log.Printf("Error creating request: %v", err)
		return nil, err
	}

	for key, value := range r.headers {
		req.Header.Set(key, value.(string))
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}

	return resp, nil
}
