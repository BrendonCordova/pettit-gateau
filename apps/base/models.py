from django.db import models
import uuid

class BaseModel(models.Model):
    '''
    Abstract base model that provides a universal UUID primary key, 
    self-updating audit timestamps ('created_at' and 'updated_at'), 
    and a soft-deletion flag ('is_active').
    
    Intended to be inherited by all other models in the system to ensure 
    schema consistency and DRY (Don't Repeat Yourself) design.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        abstract = True