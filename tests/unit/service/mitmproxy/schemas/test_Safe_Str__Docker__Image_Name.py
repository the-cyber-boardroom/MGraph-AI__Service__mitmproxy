from unittest import TestCase

from osbot_utils.type_safe.primitives.safe_str.Safe_Str import Safe_Str
from osbot_utils.utils.Objects import base_classes

from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Image_Name import Safe_Str__Docker__Image_Name


class test_Safe_Str__Docker__Image_Name(TestCase):

    def test__init__(self):                                              # Test inheritance and initialization
        with Safe_Str__Docker__Image_Name() as _:
            assert type(_)            is Safe_Str__Docker__Image_Name
            assert Safe_Str           in base_classes(_)
            assert _.max_length       == 255
            assert _.replacement_char == '-'

    def test_validate(self):                                            # Test validation rules

        # Test lowercase conversion
        assert Safe_Str__Docker__Image_Name("Ubuntu")          == "ubuntu"
        assert Safe_Str__Docker__Image_Name("NGINX")           == "nginx"

        # Test separator handling
        assert Safe_Str__Docker__Image_Name("my//image")       == "my/image"   # Multiple slashes
        assert Safe_Str__Docker__Image_Name("..image")         == "image"      # Leading dots
        assert Safe_Str__Docker__Image_Name("image--name")     == "image-name" # Multiple hyphens

        # Test registry/namespace/name format
        assert Safe_Str__Docker__Image_Name("myimage")         == "myimage"
        assert Safe_Str__Docker__Image_Name("namespace/image") == "namespace/image"
        assert Safe_Str__Docker__Image_Name("reg.io/ns/image") == "reg.io/ns/image"
        assert Safe_Str__Docker__Image_Name("a/b/c/d/e")       == "c/d/e"      # Too many parts - keep last 3

    def test_docker_image_formats(self):                                # Test various Docker image formats
        test_cases = [  ("nginx"                          , "nginx"                         ),  # Official image
                        ("library/nginx"                  , "library/nginx"                 ),  # Library namespace
                        ("myuser/myapp"                   , "myuser/myapp"                  ),  # User namespace
                        ("gcr.io/project/image"           , "gcr.io/project/image"          ),  # GCR registry
                        ("localhost:5000/myapp"           , "localhost-5000/myapp"          ),  # Local registry
                        ("docker.io/library/ubuntu"       , "docker.io/library/ubuntu"      ),  # Full Docker Hub
                        ("My-Image_v1.0"                  , "my-image_v1.0"                 ),  # Mixed case
                        ("image@sha256"                   , "image-sha256"                  ),  # @ replaced
                        ("../../../etc/passwd"            , "etc/passwd"                    ),  # Path traversal attempt
                        ("image with spaces"              , "image-with-spaces"             ),  # Spaces replaced
                        ("UPPERCASE/IMAGE/NAME"           , "uppercase/image/name"          )]  # All uppercase

        for input_value, expected in test_cases:
            with self.subTest(input=input_value):
                docker_image = Safe_Str__Docker__Image_Name(input_value)
                assert docker_image == expected

    def test_special_characters(self):                                  # Test special character handling

        # Special characters should be replaced with hyphen
        assert Safe_Str__Docker__Image_Name("my!image")        == "my-image"
        assert Safe_Str__Docker__Image_Name("test@image")      == "test-image"
        assert Safe_Str__Docker__Image_Name("app#v1")          == "app-v1"
        assert Safe_Str__Docker__Image_Name("image$name")      == "image-name"
        assert Safe_Str__Docker__Image_Name("test%app")        == "test-app"


