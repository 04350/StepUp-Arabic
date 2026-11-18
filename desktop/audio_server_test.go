package main

import (
	"bytes"
	"io/fs"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestEmbeddedAudioServesPlayableWAV(t *testing.T) {
	clips := []string{
		"msa-in-morning.wav",
		"msa-city-small.wav",
		"msa-one-day.wav",
		"msa-on-distant-planet.wav",
		"msa-their-food-is-the-same.wav",
	}
	handler := newAudioHandler(audioFiles)

	for _, clip := range clips {
		t.Run(clip, func(t *testing.T) {
			name := "audio/" + clip
			want, err := fs.ReadFile(audioFiles, name)
			if err != nil {
				t.Fatalf("embedded clip missing: %v", err)
			}
			if len(want) < 1000 {
				t.Fatalf("embedded clip is unexpectedly small: %d bytes", len(want))
			}

			request := httptest.NewRequest(http.MethodGet, "/"+name, nil)
			response := httptest.NewRecorder()
			handler.ServeHTTP(response, request)

			if response.Code != http.StatusOK {
				t.Fatalf("GET status = %d, want %d", response.Code, http.StatusOK)
			}
			if got := response.Header().Get("Content-Type"); !strings.HasPrefix(got, "audio/wav") {
				t.Fatalf("Content-Type = %q, want audio/wav", got)
			}
			if !bytes.Equal(response.Body.Bytes(), want) {
				t.Fatal("served audio bytes differ from embedded WAV")
			}
			if got := response.Header().Get("Accept-Ranges"); got != "bytes" {
				t.Fatalf("Accept-Ranges = %q, want bytes", got)
			}
		})
	}
}

func TestEmbeddedAudioSupportsByteRanges(t *testing.T) {
	handler := newAudioHandler(audioFiles)
	request := httptest.NewRequest(http.MethodGet, "/audio/msa-in-morning.wav", nil)
	request.Header.Set("Range", "bytes=0-63")
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)

	if response.Code != http.StatusPartialContent {
		t.Fatalf("range status = %d, want %d", response.Code, http.StatusPartialContent)
	}
	if response.Body.Len() != 64 {
		t.Fatalf("range body length = %d, want 64", response.Body.Len())
	}
	if !strings.HasPrefix(response.Header().Get("Content-Range"), "bytes 0-63/") {
		t.Fatalf("unexpected Content-Range: %q", response.Header().Get("Content-Range"))
	}
}

func TestEmbeddedAudioRejectsUnknownPathsAndMethods(t *testing.T) {
	handler := newAudioHandler(audioFiles)

	notFound := httptest.NewRecorder()
	handler.ServeHTTP(notFound, httptest.NewRequest(http.MethodGet, "/audio/not-installed.wav", nil))
	if notFound.Code != http.StatusNotFound {
		t.Fatalf("missing clip status = %d, want %d", notFound.Code, http.StatusNotFound)
	}

	methodNotAllowed := httptest.NewRecorder()
	handler.ServeHTTP(methodNotAllowed, httptest.NewRequest(http.MethodPost, "/audio/msa-in-morning.wav", nil))
	if methodNotAllowed.Code != http.StatusMethodNotAllowed {
		t.Fatalf("POST status = %d, want %d", methodNotAllowed.Code, http.StatusMethodNotAllowed)
	}
}

func TestEmbeddedArabicFontIsBundledAndServed(t *testing.T) {
	font, err := fs.ReadFile(audioFiles, "audio/fonts/NotoSansArabic.ttf")
	if err != nil {
		t.Fatalf("embedded Arabic font missing: %v", err)
	}
	if len(font) < 100_000 || !(bytes.Equal(font[:4], []byte{0x00, 0x01, 0x00, 0x00}) || bytes.Equal(font[:4], []byte("OTTO"))) {
		t.Fatal("embedded Arabic font is not a valid TrueType/OpenType font")
	}

	response := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/audio/fonts/NotoSansArabic.ttf", nil)
	newAudioHandler(audioFiles).ServeHTTP(response, request)
	if response.Code != http.StatusOK {
		t.Fatalf("font GET status = %d, want %d", response.Code, http.StatusOK)
	}
	if got := response.Header().Get("Content-Type"); got != "font/ttf" {
		t.Fatalf("font Content-Type = %q, want font/ttf", got)
	}
	if !bytes.Equal(response.Body.Bytes(), font) {
		t.Fatal("served font differs from embedded font")
	}
}
