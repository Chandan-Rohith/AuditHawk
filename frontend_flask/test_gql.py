import requests

query = """
mutation($email:String!,$password:String!){
    loginUser(email:$email,password:$password){
        success message token user{ id email provider }
    }
}
"""

r = requests.post(
    "http://localhost:8000/graphql/",
    json={"query": query, "variables": {"email": "test@test.com", "password": "test1234"}},
    timeout=10,
)
print("Status:", r.status_code)
print("Content-Type:", r.headers.get("content-type"))
print("Body:", r.text[:1000])
