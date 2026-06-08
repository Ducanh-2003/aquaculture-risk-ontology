from pyshacl import validate
from rdflib import Graph
from rdflib.namespace import RDF, Namespace
import pandas as pd

data_graph = Graph()
data_graph.parse("C:\\Users\\duc anh\\Desktop\\DoAnTotNghiep\\aquaculture-risk-ontology\\aqua_kg_multiPond.ttl", format="turtle")


shacl_rules = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://www.ntu.edu.vn/ontology/aqua-risk#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
ex:ObservationValidationShape
    a sh:NodeShape ;
    sh:targetClass sosa:Observation ; 
    # 1. pH
    sh:property [
        sh:path ex:hasPH ;
        sh:minCount 1 ;sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;sh:maxInclusive 14.0 ;
        sh:severity sh:Warning ;
        sh:message "CẢNH BÁO: Dữ liệu pH bị thiếu hoặc nằm ngoài khoảng 0-14!" ;
    ] ;
    # 2. DO
    sh:property [
        sh:path ex:hasDO ;
        sh:minCount 1 ;sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;sh:severity sh:Warning ;
        sh:message "CẢNH BÁO: Dữ liệu DO bị thiếu hoặc nhỏ hơn 0!" ;
    ] ;
    # 3. Temp
    sh:property [
        sh:path ex:hasTemp ;
        sh:minCount 1 ;sh:datatype xsd:float ;
        sh:severity sh:Warning ;
        sh:message "CẢNH BÁO: Bị mất kết nối cảm biến Nhiệt độ!" ;
    ] ;
    # 4. Turbidity
    sh:property [
        sh:path ex:hasTurbidity ;
        sh:datatype xsd:float ;sh:minInclusive 0.0 ;
        sh:message "CẢNH BÁO LỖI CẢM BIẾN: Độ đục (Turbidity) bị âm!" ;
    ] .
"""

conforms, results_graph, results_text = validate(
    data_graph, shacl_graph=shacl_rules, data_graph_format="turtle", 
    shacl_graph_format="turtle", inference='rdfs', 
    debug=False
)

if conforms:
    print("Không vi phạm ràng buộc nào.")
else:
    print("Có vi phạm ràng buộc.")
    print(results_text)