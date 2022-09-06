from apiflask import APIBlueprint
from app.power_model.price_model import get_price_day_ahead

"""
Use apiflask decorators

@pet_bp.get('/pets')
@pet_bp.output(PetOut(many=True))
def get_pets():
    return pets


@pet_bp.post('/pets')
@pet_bp.input(PetIn)
@pet_bp.output(PetOut, status_code=201)
def create_pet(data):
    pet_id = len(pets)
    data['id'] = pet_id
    pets.append(data)
    return pets[pet_id]
"""



power_bp = APIBlueprint('power_bp', __name__)  # tag name will be "power_bp"


@power_bp.get('/')
def get_power_prices():
    data = get_price_day_ahead()
    return data.to_json(orient='records', date_format='iso')