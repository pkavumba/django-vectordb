try:
    from rest_framework.routers import SimpleRouter
except ImportError:
    raise ImportError("rest_framework is required for the api to work")

from .views import VectorViewSet


router = SimpleRouter()
router.register(r"vectordb", VectorViewSet)

urlpatterns = router.urls
