from server import create_app


if __name__ == '__main__':
    app = create_app()
    print("Starting Michael's Chat server on http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
