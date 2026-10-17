#!/bin/sh
# Start the LangServe backend, wait for it, then start the Gradio frontend.
python server.py &
SERVER_PID=$!

until python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; do
  sleep 1
done

python app.py &
APP_PID=$!

trap "kill $SERVER_PID $APP_PID" TERM INT
wait -n
kill $SERVER_PID $APP_PID 2>/dev/null
