#!/usr/bin/env python

import os
import json

import click
import jsonschema as js
# import jsonref as jr


HERE = os.path.abspath(os.path.dirname(__file__))
SECTIONS = os.path.join(HERE, 'sections')
SCHEMA_NAME = 'rnacentral-schema.json'


def validate_secondary_structure(data):
    for entry in data['data']:
        if 'secondaryStructure' not in entry:
            continue
        assert(len(entry['secondaryStructure']) == len(entry['sequence']))


def validate_is_known_global_ids(data):
    with open('sections/data-provider.json', 'r') as raw:
        known = json.load(raw)
        known = set(known["properties"]['dataProvider']['enum'])

    for entry in data["data"]:
        gene_id = entry.get('gene', {}).get('geneId', None)
        if gene_id:
            name, _ = gene_id.split(':', 1)
            assert name in known, "Unknown database: %s" % name

        for global_id in entry.get('crossReferenceIds', []):
            name, _ = global_id.split(':', 1)
            assert name in known, "Xref to unknown db: %s" % name


# Not clear if this is actually needed.
def validate_trna_annotations(data):
    for entry in data['data']:
        isoType = entry.get('additionalAnnotations', {}).get('isoType', None)
        anticodon = entry.get('sequenceFeatures', {}).get('anticodon', None)
        if isoType or anticodon:
            assert entry['soTermId'] == 'SO:0000253'


# Unsure if we should require this, maybe make it an option? I will leave the
# code here for now.
def validate_id_format(data):
    expected = data['metaData']['dataProvider']
    for entry in data['data']:
        primary_id = entry['primaryId']
        db, _ = primary_id.split(':', 1)
        if db != expected:
            msg = "Expected %s to start with %s" % (primary_id, expected)
            raise js.ValidationError(msg)

        gene_id = entry.get('gene', {}).get('geneId', None)
        if gene_id:
            gene_db = primary_id.split(':', 1)
            assert gene_db == expected


def validate(data, schema_path, sections_path):

    with open(schema_path, 'r') as raw:
        schema = json.load(raw)

    base = 'file://%s/' % sections_path
    js.validate(
        data,
        schema,
        format_checker=js.FormatChecker(),
        resolver=js.RefResolver(base, None),
    )
    validate_secondary_structure(data)
    validate_is_known_global_ids(data)
    validate_trna_annotations(data)


@click.command()
@click.argument('filename')
@click.option('--schema', default=SCHEMA_NAME,
              help='Filename of the schema to use')
@click.option('--sections', default=SECTIONS,
              help='Directory where schema parts are kept')
def main(filename, schema=None, sections=None):
    with open(filename, 'r') as raw:
        data = json.load(raw)

    validate(data, schema, os.path.abspath(sections))


if __name__ == '__main__':
    main()
