from rest_framework.views import APIView, Request, Response, status
from rest_framework.pagination import PageNumberPagination
from pets.serializers import PetSerializer
from pets.models import Pet
from groups.models import Group
from traits.models import Trait
from traits.serializers import TraitSerializer
from django.shortcuts import get_object_or_404

class PetView(APIView, PageNumberPagination):
    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        traits = serializer.validated_data.pop("traits")

        group = serializer.validated_data.pop("group")
        
        group_obj = Group.objects.filter(scientific_name__iexact=group["scientific_name"]).first()

        if not group_obj:
            group_obj = Group.objects.create(**group)

        pet_obj = Pet.objects.create(**serializer.validated_data, group=group_obj)

        for trait_dict in traits:
            trait_obj = Trait.objects.filter(name__iexact=trait_dict["name"]).first()

            if not trait_obj:
                trait_obj = Trait.objects.create(**trait_dict)
        
            pet_obj.traits.add(trait_obj)
        
        serializer = PetSerializer(pet_obj)

        return Response(serializer.data, status.HTTP_201_CREATED)

    def get(self, request: Request) -> Response:
        get_pets = request.query_params.get('trait')

        if get_pets:
            trait = Trait.objects.filter(name=get_pets).get()
            pets = Pet.objects.filter(traits=trait).all().order_by('id')
            result_page = self.paginate_queryset(pets, request)
            serializer = PetSerializer(result_page, many=True)

            return self.get_paginated_response(serializer.data)
            
        pets = Pet.objects.all().order_by('id')
        result_page = self.paginate_queryset(pets, request)
        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)


class PetDetailView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(pet, request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        traits = serializer.validated_data.pop("traits", None)
        group = serializer.validated_data.pop("group", None)
            
        if group:
            group_obj = Group.objects.filter(scientific_name__iexact=group["scientific_name"]).first()

            if not group_obj:
                group_obj = Group.objects.create(**group)
            
            pet.group = group_obj
            pet.save()


        pet.traits.clear()

        if traits:
            for trait in traits:
                trait_obj = Trait.objects.filter(name__iexact=trait["name"]).first()

                if not trait_obj:
                    trait_obj = Trait.objects.create(**trait)
                
                pet.traits.add(trait_obj)
            
        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)
            pet.save()

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)
    
    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)