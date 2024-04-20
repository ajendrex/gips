#!/bin/bash

echo "Waiting Postgres to launch on 5432..."

while ! pg_isready -h $DATABASE_HOST -d bvc; do
    sleep 0.1 # wait for 1/10 of the second before check again
  done

  echo "Postgres launched"
