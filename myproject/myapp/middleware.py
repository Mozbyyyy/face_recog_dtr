# import requests
# from datetime import datetime

# class CurrentTimeMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         try:

#             response = requests.get('https://worldtimeapi.org/api/ip')
#             response.raise_for_status()
#             data = response.json()

#             internet_time = data.get('datetime') or data.get('utc_datetime')
#             request.current_time = datetime.strptime(internet_time, '%Y-%m-%dT%H:%M:%S.%f%z')

#             #print(f"Internet Time: {request.current_time}")
#         except requests.RequestException as e:
           
#             print(f"Failed to fetch internet time: {e}")
#             request.current_time = datetime.now()

#         response = self.get_response(request)
#         return response










from datetime import datetime

class CurrentTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        request.current_time = datetime.now()

        response = self.get_response(request)

        return response
