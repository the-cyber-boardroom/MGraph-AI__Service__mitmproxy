from unittest                                                                       import TestCase
from osbot_utils.type_safe.Type_Safe__Primitive                                     import Type_Safe__Primitive
from osbot_utils.type_safe.primitives.safe_str.Safe_Str                             import Safe_Str
from osbot_utils.utils.Objects                                                      import base_classes
from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Container_Name    import Safe_Str__Docker__Container_Name


class test_Safe_Str__Docker__Container_Name(TestCase):
    
    def test__init__(self):                                              # Test inheritance and initialization
        with Safe_Str__Docker__Container_Name() as _:
            assert type(_)          is Safe_Str__Docker__Container_Name
            assert base_classes(_)  == [Safe_Str, Type_Safe__Primitive,str, object, object]
            # max_length is passed as parameter in __new__, not class attribute
            
    def test_validate(self):                                            # Test validation rules
        # Test lowercase conversion
        assert Safe_Str__Docker__Container_Name("MyContainer")     == "mycontainer"
        assert Safe_Str__Docker__Container_Name("UPPERCASE")       == "uppercase"
        assert Safe_Str__Docker__Container_Name("Mixed-Case_123")  == "mixed-case_123"
        
    def test_docker_compliant_names(self):                              # Test Docker-compliant container names
        test_cases = [("nginx"               , "nginx"               ),            # Simple name
                      ("my-app"              , "my-app"              ),            # With hyphen
                      ("web_server"          , "web_server"          ),            # With underscore
                      ("app.v1"              , "app.v1"              ),            # With period
                      ("my-app-123"          , "my-app-123"          ),            # With numbers
                      ("MyApp"               , "myapp"               ),            # Uppercase to lowercase
                      ("my--app"             , "my--app"             ),            # Double hyphen work ok
                      ("123-start"           , "123-start"           ),            # Can start with number
                      ("test!@#$%"           , "test_____"           )]            # Special chars replaced


        
        for input_value, expected in test_cases:
            with self.subTest(input=input_value):
                container_name = Safe_Str__Docker__Container_Name(input_value)
                assert container_name == expected
                
    def test_empty_and_none(self):                                      # Test edge cases
        assert Safe_Str__Docker__Container_Name("")   == ""
        assert Safe_Str__Docker__Container_Name(None) == ""