from copy import deepcopy


class SwaggerModelGeneratorError(Exception):
    pass


MODEL_LIBS = {}


class Transformer:
    def __init__(self, schema: dict):
        self._schemas = schema

    def expand_schema(self, schema: dict) -> dict:
        for model_name, model in schema.copy().items():
            expanded_model = self.expand_schema_model(model)
            schema[model_name] = expanded_model  # TODO:Refactor
            self._schemas[model_name] = expanded_model
        return self._schemas

    def expand_schema_model(self, model: dict) -> dict:
        schema_model = self._merge_model(model) if 'allOf' in model else deepcopy(model)
        if 'properties' in schema_model:
            schema_model['properties'] = self._expand_props(schema_model['properties'])
        if 'items' in schema_model:
            schema_model['items'] = self.expand_schema_model(schema_model['items'])
        return schema_model

    def _merge_model(self, model: dict) -> dict:
        all_of_obj = model.pop('allOf')
        base_model_name = all_of_obj[0]['$ref'].split('/')[-1]
        base_model = self._schemas[base_model_name]

        merged_model = deepcopy(base_model)
        merged_model.update(model)

        if len(all_of_obj) > 1:
            model_all_of_obj = all_of_obj[1]
            if 'properties' in model_all_of_obj:
                merged_model['properties'].update(model_all_of_obj['properties'])
            if 'required' in model_all_of_obj:
                merged_model['required'] = model_all_of_obj['required']
        return merged_model

    def _expand_props(self, props: dict) -> dict:
        return {k: self.expand_schema_model(v) for k, v in props.items()}


class Generator:
    _schemas = {}

    def __init__(
            self,
            models_dir,
            models_lib='schematics',
            base_model=object,
            additional_props=None,
            additional_defaults=None
    ):
        self.models_dir = models_dir
        self.models_lib = models_lib
        self.base_model = base_model
        self.additional_props = additional_props
        self.additional_defaults = additional_defaults

    @property
    def builder_cls(self):
        return MODEL_LIBS[self.models_lib]

    @property
    def schemas(self):
        return self._schemas

    def get_builder(self, module):
        return self.builder_cls(self.schemas, module)

    def build(self, schema, module):
        self._transform(schema)
        self.get_builder(module).generate_schema_from_swagger(schema)

    def _transform(self, schema):
        return Transformer(self.schemas).expand_schema(schema)

    def _update(self, schema):
        self.schemas.update(schema)
