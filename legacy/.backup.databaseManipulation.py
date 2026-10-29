
from spotify import authenticate, get_recommendations
from database import save

def main():
    access_token = authenticate()
    data = get_recommendations(access_token)
    save(data)

if __name__ == '__main__':
    main()
