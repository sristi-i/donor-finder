#!/usr/bin/env bash
curl -X POST "http://localhost:8000/donors/ingest/propublica?state=CA&ntee_major=2&limit=35"
curl -X POST "http://localhost:8000/donors/embeddings/build?batch_size=32&max_rows=500"
