from copy import deepcopy


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
