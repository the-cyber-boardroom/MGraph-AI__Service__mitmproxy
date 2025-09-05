from unittest                                                         import TestCase
from osbot_utils.type_safe.primitives.safe_str.Safe_Str               import Safe_Str
from osbot_utils.utils.Objects                                        import base_classes
from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Tag import Safe_Str__Docker__Tag


class test_Safe_Str__Docker__Tag(TestCase):

    def test__init__(self):                                              # Test inheritance and initialization
        with Safe_Str__Docker__Tag()  as _:
            assert type(_)            is Safe_Str__Docker__Tag
            assert Safe_Str           in base_classes(_)
            assert _.max_length       == 128
            assert _.replacement_char == '-'

    def test__new__transformations(self):                               # Test transformations in __new__
        # Test empty becomes latest
        assert Safe_Str__Docker__Tag("")     == "latest"
        assert Safe_Str__Docker__Tag(None)   == "latest"                 # None also becomes latest

        # Test separator handling happens in __new__
        assert Safe_Str__Docker__Tag("..v1")     == "v1"                # Leading dots removed
        assert Safe_Str__Docker__Tag("v1--2")    == "v1-2"              # Multiple hyphens
        assert Safe_Str__Docker__Tag("tag__name") == "tag_name"         # Underscores preserved

        # Test sha256 special case
        assert Safe_Str__Docker__Tag("sha256:abc123") == "sha256:abc123" # Preserve sha256: prefix

    def test_docker_tag_formats(self):                                  # Test various Docker tag formats
        test_cases = [
            ("latest"                         , "latest"                        ),  # Most common
            ("v1.0.0"                         , "v1.0.0"                        ),  # Semantic version
            ("1.0"                            , "1.0"                           ),  # Simple version
            ("20240101"                       , "20240101"                      ),  # Date format
            ("2024-01-01"                     , "2024-01-01"                    ),  # Date with hyphens
            ("develop"                        , "develop"                       ),  # Branch name
            ("feature-branch"                 , "feature-branch"                ),  # Branch with hyphen
            ("rc-1.0"                         , "rc-1.0"                        ),  # Release candidate
            ("sha256:a1b2c3"                 , "sha256:a1b2c3"                 ),  # SHA format
            ("LATEST"                         , "LATEST"                        ),  # Uppercase preserved
            ("V1.0.0"                         , "V1.0.0"                        ),  # Uppercase version
            ("my tag"                         , "my-tag"                        ),  # Space replaced
            ("tag@version"                    , "tag-version"                   ),  # @ replaced
            ("../../../etc"                   , "etc"                           ),  # Path traversal
            (""                               , "latest"                        ),  # Empty becomes latest
        ]

        for input_value, expected in test_cases:
            with self.subTest(input=input_value):
                docker_tag = Safe_Str__Docker__Tag(input_value)
                assert docker_tag == expected

    def test_special_tags(self):                                        # Test special Docker tags
        # SHA256 tags
        sha_tag = Safe_Str__Docker__Tag("sha256:abcdef1234567890")
        assert sha_tag == "sha256:abcdef1234567890"

        # Git commit hash
        git_tag = Safe_Str__Docker__Tag("git-a1b2c3d")
        assert git_tag == "git-a1b2c3d"

        # Build number
        build_tag = Safe_Str__Docker__Tag("build-12345")
        assert build_tag == "build-12345"

    def test_max_length(self):                                          # Test max length enforcement
        long_tag = "v" + "1" * 200                                      # Way over 128 chars
        docker_tag = Safe_Str__Docker__Tag(long_tag)
        assert len(docker_tag) <= 128
        assert docker_tag.startswith("v1111")                           # Content preserved up to limit


