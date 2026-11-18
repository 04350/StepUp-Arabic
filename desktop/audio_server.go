package main

import (
	"bytes"
	"embed"
	"io/fs"
	"mime"
	"net/http"
	"path"
	"strings"
	"time"
)

// Audio files are embedded into the Windows executable at build time.
//go:embed audio/*
var audioFiles embed.FS

// newAudioHandler serves embedded audio with explicit media MIME types and
// byte-range support required by browser media elements.
func newAudioHandler(files fs.FS) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", "GET, HEAD")
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		assetPath := strings.TrimPrefix(r.URL.Path, "/")
		if !strings.HasPrefix(assetPath, "audio/") || !fs.ValidPath(assetPath) || strings.Contains(assetPath, "\\") {
			http.NotFound(w, r)
			return
		}

		data, err := fs.ReadFile(files, assetPath)
		if err != nil {
			http.NotFound(w, r)
			return
		}

		extension := strings.ToLower(path.Ext(assetPath))
		contentType := ""
		switch extension {
		case ".wav":
			contentType = "audio/wav"
		case ".mp3":
			contentType = "audio/mpeg"
		case ".ogg", ".oga":
			contentType = "audio/ogg"
		case ".m4a":
			contentType = "audio/mp4"
		case ".ttf":
			contentType = "font/ttf"
		case ".otf":
			contentType = "font/otf"
		case ".woff":
			contentType = "font/woff"
		case ".woff2":
			contentType = "font/woff2"
		default:
			contentType = mime.TypeByExtension(extension)
		}
		if contentType == "" {
			contentType = "application/octet-stream"
		}

		w.Header().Set("Content-Type", contentType)
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
		w.Header().Set("Accept-Ranges", "bytes")
		http.ServeContent(w, r, path.Base(assetPath), time.Time{}, bytes.NewReader(data))
	})
}
