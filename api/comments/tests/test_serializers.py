import pytest
from django.contrib.auth import get_user_model

from api.lead_status.models import LeadStatus
from api.leads.models import Lead
from api.comments.serializers import CommentSerializer
from rest_framework.test import APIRequestFactory

@pytest.mark.django_db
def test_comment_serializer_create_valid():
    user = get_user_model().objects.create_user(email="a@a.fr", first_name="A", last_name="B", password="pwd")
    status = LeadStatus.objects.create(code="RDV_PLANIFIE", label="Planifié", color="#333")
    lead = Lead.objects.create(first_name="A", last_name="B", phone="+33612345678", status=status)
    data = {"lead_id": lead.id, "content": "Un commentaire utile"}
    factory = APIRequestFactory()
    request = factory.post("/comments/", data)
    request.user = user
    serializer = CommentSerializer(data=data, context={"request": request})
    assert serializer.is_valid(), serializer.errors
    comment = serializer.save()
    assert comment.content == "Un commentaire utile"
    assert comment.author == user