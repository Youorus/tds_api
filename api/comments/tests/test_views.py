import pytest
from django.contrib.auth import get_user_model
from api.lead_status.models import LeadStatus
from api.leads.models import Lead
from api.comments.models import Comment

@pytest.mark.django_db
def test_create_comment_api(client):
    user = get_user_model().objects.create_user(email="test@x.fr", first_name="A", last_name="B", password="pwd")
    status = LeadStatus.objects.create(code="RDV_PLANIFIE", label="Planifié", color="#333")
    lead = Lead.objects.create(first_name="F", last_name="L", phone="+33611111111", status=status)
    client.force_authenticate(user=user)
    resp = client.post("/api/comments/", {"lead_id": lead.id, "content": "Coucou !"})
    assert resp.status_code == 201
    assert resp.data["content"] == "Coucou !"

@pytest.mark.django_db
def test_list_comments_by_lead(client):
    user = get_user_model().objects.create_user(email="xx@yy.fr", first_name="A", last_name="B", password="pwd")
    status = LeadStatus.objects.create(code="RDV_PLANIFIE", label="Planifié", color="#333")
    lead = Lead.objects.create(first_name="F", last_name="L", phone="+33611111111", status=status)
    Comment.objects.create(lead=lead, author=user, content="Test 1")
    Comment.objects.create(lead=lead, author=user, content="Test 2")
    client.force_authenticate(user=user)
    resp = client.get(f"/api/comments/lead/{lead.id}/")
    assert resp.status_code == 200
    assert len(resp.data) == 2

@pytest.mark.django_db
def test_cannot_edit_or_delete_other_comment(client):
    user1 = get_user_model().objects.create_user(email="u1@a.fr", first_name="A", last_name="B", password="pwd")
    user2 = get_user_model().objects.create_user(email="u2@a.fr", first_name="C", last_name="D", password="pwd")
    status = LeadStatus.objects.create(code="RDV_PLANIFIE", label="Planifié", color="#333")
    lead = Lead.objects.create(first_name="F", last_name="L", phone="+33611111111", status=status)
    comment = Comment.objects.create(lead=lead, author=user1, content="Interdit !")
    client.force_authenticate(user=user2)
    resp = client.patch(f"/api/comments/{comment.id}/", {"content": "Hack"}, format="json")
    assert resp.status_code == 403
    resp = client.delete(f"/api/comments/{comment.id}/")
    assert resp.status_code == 403