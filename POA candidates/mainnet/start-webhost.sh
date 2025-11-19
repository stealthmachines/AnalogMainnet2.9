#!/bin/bash

# Define network name with project prefix to avoid conflicts
NETWORK_NAME="hdgl_network_v2"

# Function to clean up resources
cleanup() {
    echo "Stopping HDGL services..."
    docker compose -f docker-compose.webhost.yml down

    echo "Removing HDGL network..."
    docker network rm $NETWORK_NAME || true

    echo "Cleanup complete"
}

# Handle command line arguments
case "$1" in
    start)
        # Create the network if it doesn't exist
        echo "Setting up HDGL network..."
        docker network create $NETWORK_NAME 2>/dev/null || true

        # Start services
        echo "Starting HDGL services..."
        docker compose -f docker-compose.webhost.yml up -d

        echo "HDGL services are running:"
        echo "- Stats Dashboard:      http://localhost:8547"
        echo "- Network Explorer:     http://localhost:8548"
        echo "- Network Visualizer:   http://localhost:8549"
        echo "- Program Interface:    http://localhost:8550"
        ;;

    stop)
        echo "Stopping HDGL services..."
        docker compose -f docker-compose.webhost.yml down
        ;;

    cleanup)
        cleanup
        ;;

    status)
        echo "HDGL Services Status:"
        echo "-------------------"
        docker ps --filter "name=hdgl_.*_v2" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo "Network Status:"
        echo "--------------"
        docker network ls | grep "hdgl_network_v2" || echo "Network not found"
        ;;

    logs)
        if [ -z "$2" ]; then
            echo "Usage: $0 logs [stats|explorer|visualizer|program]"
            exit 1
        fi
        docker logs "hdgl_${2}_v2" --tail 100 -f
        ;;

    *)
        echo "Usage: $0 {start|stop|cleanup|status|logs}"
        echo "  start   - Start HDGL services"
        echo "  stop    - Stop HDGL services"
        echo "  cleanup - Stop services and remove network"
        echo "  status  - Show running HDGL services"
        echo "  logs    - Show logs for a specific service (stats|explorer|visualizer|program)"
        echo "  start   - Start HDGL services"
        echo "  stop    - Stop HDGL services"
        echo "  cleanup - Stop services and remove network"
        echo "  status  - Show running HDGL services"
        exit 1
        ;;
esac