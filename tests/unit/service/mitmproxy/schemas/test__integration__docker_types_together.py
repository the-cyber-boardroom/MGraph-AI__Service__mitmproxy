from unittest                                                                    import TestCase
from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Container_Name import Safe_Str__Docker__Container_Name
from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Image_Name     import Safe_Str__Docker__Image_Name
from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Tag            import Safe_Str__Docker__Tag


class test__integration__docker_types_together(TestCase):

    def test_complete_docker_reference(self):                           # Test complete Docker image reference
        # Format: registry/namespace/image:tag

        # Create components
        container_name = Safe_Str__Docker__Container_Name("My-Test_Container!")
        image_name     = Safe_Str__Docker__Image_Name("gcr.io/my-project/my-app@latest")
        tag            = Safe_Str__Docker__Tag("v1.0.0-beta")

        # Verify sanitization
        assert container_name == "my-test_container_"
        assert image_name     == "gcr.io/my-project/my-app-latest"
        assert tag           == "v1.0.0-beta"

        # Compose full reference
        full_reference = f"{image_name}:{tag}"
        assert full_reference == "gcr.io/my-project/my-app-latest:v1.0.0-beta"

    def test_docker_compose_compatibility(self):                         # Test docker-compose.yml compatibility
        # docker-compose service names have similar rules to container names
        service_names = [
            "web_server",
            "database-01",
            "cache.redis",
            "my-app_v2"
        ]

        for name in service_names:
            container_name = Safe_Str__Docker__Container_Name(name)
            assert container_name == name.lower()                       # All valid, just lowercased

    def test_kubernetes_compatibility(self):                            # Test Kubernetes naming compatibility
        # Kubernetes has stricter rules but should work with our types
        k8s_names = [
            "nginx-deployment",
            "redis-master",
            "web-service-v1",
            "backend-api-123"
        ]

        for name in k8s_names:
            container_name = Safe_Str__Docker__Container_Name(name)
            # Should preserve valid k8s names
            assert container_name == name.lower()
            assert len(container_name) <= 253                           # K8s limit