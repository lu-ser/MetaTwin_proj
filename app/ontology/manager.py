# app/ontology/manager.py
import json
import os
from typing import Dict, List, Any, Optional, Set
from app.config import settings

class OntologyManager:
    """Gestisce l'ontologia e le sue relazioni"""
    
    def __init__(self, ontology_path: str = None):
        """Inizializza il gestore dell'ontologia"""
        if not ontology_path:
            # Usa il percorso dal file di configurazione
            ontology_path = settings.CLASS_HIERARCHY_PATH
        
        with open(ontology_path, "r") as f:
            self.class_hierarchy = json.load(f)
            
        # Costruisci il grafo delle relazioni inverse (da superclass a subclass)
        self.subclass_relations = {}
        for class_name, details in self.class_hierarchy.items():
            for superclass in details.get("superclass", []):
                if superclass not in self.subclass_relations:
                    self.subclass_relations[superclass] = []
                self.subclass_relations[superclass].append(class_name)
    
    def get_sensor_details(self, sensor_type: str) -> Optional[Dict[str, Any]]:
        """Ottiene i dettagli di un tipo di sensore dall'ontologia"""
        return self.class_hierarchy.get(sensor_type)
    
    def get_all_sensor_types(self) -> List[str]:
        """Ottiene tutti i tipi di sensore definiti nell'ontologia"""
        return list(self.class_hierarchy.keys())
    
    def get_root_classes(self) -> List[str]:
        """Ottiene le classi radice (senza superclass) dall'ontologia"""
        return [class_name for class_name, details in self.class_hierarchy.items() 
                if not details.get("superclass")]
    
    def get_subclasses(self, class_name: str) -> List[str]:
        """Ottiene tutte le sottoclassi dirette di una classe"""
        return self.subclass_relations.get(class_name, [])
    
    def get_all_subclasses(self, class_name: str) -> List[str]:
        """Ottiene tutte le sottoclassi (recursive) di una classe"""
        result = []
        direct_subclasses = self.get_subclasses(class_name)
        result.extend(direct_subclasses)
        
        for subclass in direct_subclasses:
            result.extend(self.get_all_subclasses(subclass))
            
        return list(set(result))  # Rimuovi duplicati
    
    def get_all_superclasses(self, class_name: str) -> List[str]:
        """Ottiene tutte le superclassi (recursive) di una classe"""
        if class_name not in self.class_hierarchy:
            return []
            
        result = []
        direct_superclasses = self.class_hierarchy[class_name].get("superclass", [])
        result.extend(direct_superclasses)
        
        for superclass in direct_superclasses:
            result.extend(self.get_all_superclasses(superclass))
            
        return list(set(result))  # Rimuovi duplicati
    
    def is_sensor_compatible(self, device_type: str, sensor_type: str) -> bool:
        """Verifica se un sensore è compatibile con un tipo di dispositivo"""
        # Se il dispositivo è un tipo di sensore nell'ontologia
        if device_type in self.class_hierarchy:
            # Controlla se il tipo di sensore è il dispositivo stesso o una sua sottoclasse
            if sensor_type == device_type:
                return True
                
            # Controlla se il tipo di sensore è una superclasse del dispositivo
            superclasses = self.get_all_superclasses(device_type)
            if sensor_type in superclasses:
                return True
                
            # Controlla se il tipo di sensore è una sottoclasse del dispositivo
            subclasses = self.get_all_subclasses(device_type)
            if sensor_type in subclasses:
                return True
                
        return False
    
    def get_compatible_sensors(self, device_type: str) -> List[str]:
        """Ottiene tutti i tipi di sensori compatibili con un tipo di dispositivo"""
        compatible_sensors = []
        
        # Se il dispositivo è un tipo di sensore nell'ontologia
        if device_type in self.class_hierarchy:
            # Aggiungi il dispositivo stesso
            compatible_sensors.append(device_type)
            
            # Aggiungi tutte le superclassi
            compatible_sensors.extend(self.get_all_superclasses(device_type))
            
            # Aggiungi tutte le sottoclassi
            compatible_sensors.extend(self.get_all_subclasses(device_type))
            
        return list(set(compatible_sensors))  # Rimuovi duplicati
    
    def generate_random_value_for_sensor(self, sensor_type: str) -> Optional[float]:
        """Genera un valore casuale per un tipo di sensore basato sui suoi parametri nell'ontologia"""
        import random
        
        if sensor_type not in self.class_hierarchy:
            return None
            
        sensor_details = self.class_hierarchy[sensor_type]
        
        # Verifica se ci sono limiti min e max definiti
        if "min" in sensor_details and "max" in sensor_details:
            min_val = sensor_details["min"]
            max_val = sensor_details["max"]
            
            # Usa il valore medio se disponibile, altrimenti calcola la media
            mean_val = sensor_details.get("mean", (min_val + max_val) / 2)
            
            # Genera un valore casuale con distribuzione gaussiana
            # Usa (max - min) / 6 come deviazione standard per mantenere la maggior parte
            # dei valori all'interno del range (circa 99.7% dei valori)
            std_dev = (max_val - min_val) / 6
            value = random.gauss(mean_val, std_dev)
            
            # Assicurati che il valore sia entro i limiti
            value = max(min_val, min(max_val, value))
            
            return round(value, 2)
            
        return None