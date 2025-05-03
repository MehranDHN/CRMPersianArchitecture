import json
import requests
import os
import logging
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from uuid import uuid4
from urllib.parse import urlparse
import traceback
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# URL of the JSON file containing TEI XML records
JSON_URL = "https://raw.githubusercontent.com/MehranDHN/CRMPersianArchitecture/refs/heads/main/tei_xml_records.json"


# Define namespaces
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
MS = Namespace("http://example.org/ontology/manuscript#")
AAT = Namespace("http://vocab.getty.edu/aat/")
LCSH = Namespace("http://id.loc.gov/authorities/subjects/")
WD = Namespace("http://www.wikidata.org/entity/")
EX = Namespace("http://example.org/resource/")
SC = Namespace("https://schema.org/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
MDHN = Namespace("http://example.com/mdhn/")

def get_filename_from_url(url):
    """Extract the filename from a URL."""
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)

def safe_get(data, *keys, default="Unknown"):
    """Safely access nested dictionary keys, handling strings, lists, and other types."""
    current = data
    path = []
    for key in keys:
        path.append(key)
        try:
            if isinstance(current, str):
                logger.debug(f"Encountered string at path {path}: {current}")
                print(f"Encountered string at path {path}: {current}")
                return current if current else default
            elif isinstance(current, list):
                current = current[0] if current else default
            elif isinstance(current, dict):
                current = current.get(key, default)
            else:
                logger.warning(f"Unexpected type {type(current)} at path {path}: {current}")
                print(f"Unexpected type {type(current)} at path {path}: {current}")
                return default
        except (TypeError, IndexError) as e:
            logger.warning(f"Error accessing path {path}: {str(e)}")
            print("Error accessing path {path}: {str(e)}")
            return default
    return current if current != default else default

def read_local_json_file(file_path):
    try:
       logger.info(f"Reading local JSON file: {file_path}")
       with open(file_path, "r", encoding="utf-8") as f:
          json_data = json.load(f)
       return json_data
    except Exception as e:
       logger.error(f"Failed to process {file_path}: {str(e)}")

def create_publisher_graph(graph, publisher_name):
    """Create RDF triples for the publisher."""
    #publisher_id = str(uuid4())  # Generate a unique ID for the publisher
    publisher_id = publisher_name.replace(" ", "_").replace(",", "").replace("&","").replace(".","_").strip()
    publisher_uri = URIRef(f"http://example.com/mdhn/{publisher_id}")
    graph.add((publisher_uri, RDF.type, SC.Organization))
    graph.add((publisher_uri, RDFS.label, Literal(publisher_name, lang="en")))
    return publisher_uri

def create_manuscript_graph(graph, publisheruri, manuscriptID, teiXMLURL):
    """Create RDF triples for the manuscript."""
    global total_Images
    #collectionid = teiXMLURL.replace("https://openn.library.upenn.edu/Data/","")[0:4]
    lastidx = teiXMLURL.rfind('/')  
    imageprefix = teiXMLURL.strip()[0:lastidx]
    output_dir = "i:\\IAPython\\AAT\TEIXml\\tei_json_output"
    #https://openn.library.upenn.edu/Data/0003/bv_051/data/thumb/9710_0008_thumb.jpg
    idforPath = manuscriptID.replace(" ", "_")

    xml_filename = get_filename_from_url(teiXMLURL)
    json_filename = os.path.splitext(xml_filename)[0] + ".json"
    output_path = os.path.join(output_dir, json_filename)
    logger.info("Based on " + teiXMLURL + " JSON= " + output_path)
    manuscript_uri = ""
    illustrationDict = {"test" : "test"}
    if os.path.exists(output_path):
        json_data = read_local_json_file(output_path)
        language = safe_get(json_data, "TEI", "teiHeader", "fileDesc", "sourceDesc", "msDesc", "msContents", "textLang", "@mainLang", default="Unknown Language")
        choMsContents = safe_get(json_data, "TEI", "teiHeader", "fileDesc", "sourceDesc", "msDesc", "msContents", default={})
        choMsItem = safe_get(json_data, "TEI", "teiHeader", "fileDesc", "sourceDesc", "msDesc", "msContents", "msItem", default=[])
        choDecoNote = safe_get(json_data, "TEI", "teiHeader", "fileDesc", "sourceDesc", "msDesc", "physDesc","decoDesc","decoNote", default=[])  
        print("Safe Here 1")
        if isinstance(choDecoNote, list) :
            for note in choDecoNote :
                if isinstance(note, str):
                    # Ignoring the text value
                    z=0
                elif isinstance(note, dict):
                    k = safe_get(note, "@n").strip()
                    v = safe_get(note, "#text").strip()
                    print(f'\t key={k} value={v}')
                    if k not in illustrationDict:
                       illustrationDict[k] = v
        else:
            print("Ignoring DecoNote canvas types")                   

        print("Safe Here 2")
        choTitle = ""
        if isinstance(choMsItem[0], dict) and "title" in choMsItem[0]:
           print("choMsItem is dict")
           choTitle = safe_get(choMsItem[0], "title")
        else:
            print("Not safe here No Title found")
        choTitleText = ""
        choTitleNativeText = ""
        hasNativeTitle = False
        choSummary = ""
        print("Safe Here 2.5")
        if isinstance(choMsContents, dict) and "summary" in choMsContents:
           choSummary = safe_get(choMsContents, "summary")
           if isinstance(choSummary, str) :
               choSummary = choSummary.strip()
        else:
            print("Not dafe here No Summary found")
        print("Safe Here 3")

        if isinstance(choTitle, str) : 
            if choTitle :
               choTitleText = choTitle.strip() 
            else:
                choTitleText = "Unknown Title"
        elif isinstance(choTitle, list):
            hasNativeTitle = True
            if choTitle :
               choTitleText = choTitle[0].strip() 
               choTitleNativeText = safe_get(choTitle[1], "#text").strip()
            else:
                choTitleText = "Unknown Title"
                choTitleNativeText ="بدون عنوان"
        print("Safe Here 4")
        canvases = safe_get(json_data, "TEI", "facsimile", "surface", default=[])
        print(len(canvases))
        total_Images += len(canvases)
        manuscript_id = manuscriptID.replace(" ", "_").replace(",", "").replace("&","").replace(".","_").replace("-","").replace("[","").replace("]", "").replace("/", "").strip()
        manuscript_uri = URIRef(f"http://example.com/mdhn/{manuscript_id}")
        graph.add((manuscript_uri, RDF.type, SC.CreativeWork)) 
        graph.add((manuscript_uri, RDFS.label, Literal(choTitleText, lang="en")))
        if hasNativeTitle: 
            graph.add((manuscript_uri, RDFS.label, Literal(choTitleNativeText, lang="fa")))   
        graph.add((manuscript_uri, RDFS.comment, Literal(choSummary, lang="en")))                   
        graph.add((manuscript_uri, SC.identifier, Literal(manuscriptID, lang="en")))
        graph.add((manuscript_uri, SC.publisher, publisheruri))
        graph.add((manuscript_uri, SC.additionalType, Literal(teiXMLURL, lang="en"))) 
        graph.add((manuscript_uri, SC.inLanguage, Literal(language, lang="en")))  
        print("Safe Here 5")
        if len(canvases)>0:
            tempThumb = safe_get(canvases[0], "graphic")
            thumbUrl = safe_get(tempThumb[1], "@url")
            fullThumbURL = f'{imageprefix}/{thumbUrl}'
            graph.add((manuscript_uri, SC.image, Literal(fullThumbURL, lang="en")))      
            graph.add((manuscript_uri, SC.numberOfPages, Literal(len(canvases), datatype=XSD.integer)))
            for canvas in canvases:
                canvasLabel = safe_get(canvas, "@n")
                canvasRepresentation = safe_get(canvas, "graphic")
                canvasMasterHeight = safe_get(canvasRepresentation[0], "@height")
                canvasMasterUrl = safe_get(canvasRepresentation[0], "@url")
                canvasMasterWidth = safe_get(canvasRepresentation[0], "@width") 
                canvasThumbHeight = safe_get(canvasRepresentation[1], "@height")
                canvasThumbUrl = safe_get(canvasRepresentation[1], "@url")
                canvasThumbWidth = safe_get(canvasRepresentation[1], "@width")  
                canvasWebHeight = safe_get(canvasRepresentation[2], "@height")
                canvasWebUrl = safe_get(canvasRepresentation[2], "@url")
                canvasWebWidth = safe_get(canvasRepresentation[2], "@width")
                fullWebURL = f'{imageprefix}/{canvasWebUrl}' 
                canvasid = canvasMasterUrl.replace(".tif","").replace("/","_")
                canvas_uri = URIRef(f"http://example.com/mdhn/{canvasid}")
                graph.add((canvas_uri, RDF.type, SC.VisualArtwork)) 
                graph.add((canvas_uri, RDFS.label, Literal(canvasLabel, lang="en"))) 
                graph.add((canvas_uri, SC.isPartOf, manuscript_uri)) 
                graph.add((canvas_uri, SC.image, Literal(fullWebURL, lang="en")))                
                graph.add((canvas_uri, SC.height, Literal(canvasMasterHeight)))
                graph.add((canvas_uri, SC.weight, Literal(canvasMasterWidth)))
                if canvasLabel in illustrationDict:  
                   if canvasLabel.strip() in illustrationDict:
                       graph.add((canvas_uri, SC.artform, Literal(illustrationDict.get(canvasLabel.strip(), "Canvas Type"), lang="en"))) 
                   else:
                       graph.add((canvas_uri, SC.artform, Literal("Unknown Canvas Type", lang="en"))) 
                else:
                    graph.add((canvas_uri, SC.artform, Literal("Ordinary", lang="en")))
                        

    else:
        logger.warning(output_path + " Not Exists")
                    
    return manuscript_uri 

def make_uri_from_keyword(taxonomy):
    taxonomy_id = taxonomy[0].replace("ʼ","").replace("'","").replace(" ","_").replace(",","").replace("=","").replace("(","").replace(")","").replace("-","_").replace("ʻ","").replace(".","").replace("MuhÌ£ammad","Muhiammad").strip()
    taxonomy_uri = URIRef(f"http://example.com/mdhn/{taxonomy_id}")
    return taxonomy_uri
def add_subject_node(jsondata, graph, choURI):
    f=0  
    keywords = safe_get(jsondata,"TEI","teiHeader", "profileDesc", "textClass", "keywords", default=[])
    if isinstance(keywords, list):
       for item in keywords:
            level1key = safe_get(item,"@n")
            level1subjects= safe_get(item,"term", default=[])
            if level1key=="subjects" :
                b=0
                for subject in level1subjects:
                    subTerget = safe_get(subject,"@target", default="")
                    subText = safe_get(subject,"#text", default="")
                    if subText.strip().find("--")>0:
                        mlist =  subText.split("--") 
                        subjecturi = make_uri_from_keyword(mlist[-1])
                        graph.add((choURI, SC.about, subjecturi))                
            elif level1key=="form/genre":
                #Ignore genre list
                c=0
def run_pipeline():    
    i = 0 
    global total_Images
    total_Images = 0 
    # Initialize RDF graph
    g = Graph()
    g.bind("crm", CRM)
    g.bind("ms", MS)
    g.bind("aat", AAT)
    g.bind("lcsh", LCSH)
    g.bind("wd", WD)
    g.bind("ex", EX)
    g.bind("sc", SC)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    g.bind("mdhn", MDHN)

    object_id = ""
    try:
       # Fetch the JSON file
       response = requests.get(JSON_URL)
       response.raise_for_status()
       records = response.json()
       for record in records:
           i += 1
           # Extract the TEI XML URL and Object ID
           institute_name = record.get("institute_name")
           tei_xml_url = record.get("tei_xml_url")           
           object_id = record.get("object_id")
           object_name = record.get("object_name")
           if object_id!="Misc. Ms. Collection Temple Bowdon" and object_id!="961.F.5d" and object_id!="Lewis C 1" and object_id!="Lewis C 2" and object_id!="Lewis C 6" and object_id!="Lewis C 16" and object_id!="Lewis C 17" and object_id!="Lewis C 18" and object_id!="Lewis C 19" and object_id!="Lewis C 25" and object_id!="Lewis C 21" and object_id!="Lewis C 22" and object_id!="Lewis C 23" and object_id!="Lewis C 24" and object_id!="Lewis C 25" and object_id!="Lewis C 26" and object_id!="Lewis C 27" and object_id!="Lewis C 28" and object_id!="Lewis C 29"  and object_id!="Lewis M 7":
              publisherid = create_publisher_graph(g, institute_name)
              manuscriptid = create_manuscript_graph(g, publisherid, object_id, tei_xml_url)
              logger.info(f"Processing {i} - {object_id} - {institute_name} - {tei_xml_url}")
           # Get the filename and create output path


       g.serialize(destination="I:\\IAPython\\AAT\\TEIXml\\Pensylvania_RDF_Data.ttl", format="turtle")
       print("\nRDF Graph in Turtle Format:")  
       #print(turtle_output)  
       print(total_Images)        
    except requests.RequestException as e:
        print(f"Failed to fetch JSON from {JSON_URL}: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from {JSON_URL}: {e}")
    except KeyError as e: 
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = exc_traceback.tb_lineno        
        print(f"KeyError error: {e} value: {exc_value} LineNo={line_number} Objectid={object_id} images= {total_Images}")       
    except Exception as e:
        print(f"Very Unexpected error: {type(e)} args: {e.args} Objectid={object_id} images= {total_Images}")  


run_pipeline()  
         