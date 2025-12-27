#!/usr/bin/env python3
"""
Enhanced Q&A Generator Module
Generates diverse, context-aware Q&A pairs from technical entities
"""

import re
import json
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from entity_extractor import TechnicalEntity, EntityType
from table_reconstructor import Table

@dataclass
class QAPair:
    question: str
    answer: str
    category: str  # factual, troubleshooting, integration, comparison
    difficulty: str  # basic, intermediate, advanced
    metadata: Optional[Dict] = None

class EnhancedQAGenerator:
    """Generate diverse Q&A pairs from technical entities"""
    
    def __init__(self):
        # Question templates by entity type and category
        self.templates = {
            EntityType.PIN: {
                'factual': [
                    ("What is the function of {name}?", "{value}"),
                    ("What signal is present on {name}?", "{value}"),
                    ("Describe the purpose of {name}.", "{name} provides {value} functionality."),
                ],
                'reverse_lookup': [
                    ("Which pin provides {value} functionality?", "{name}"),
                    ("Where can I find the {value} signal?", "The {value} signal is available on {name}."),
                    ("What is the pin assignment for {value}?", "{value} is assigned to {name}."),
                ],
                'troubleshooting': [
                    ("What should I check if {name} is not functioning correctly?", 
                     "Verify that {name} is properly connected and providing {value}. Check for proper voltage levels and ensure no shorts to ground or adjacent pins."),
                    ("How can I test if {name} is working?", 
                     "To test {name}, measure the signal for {value} using an oscilloscope or logic analyzer. Ensure the pin is not floating and has proper pull-up/pull-down resistors if required."),
                ],
                'integration': [
                    ("How does {name} interface with the system?", 
                     "{name} provides {value}, which interfaces with the system through... [Additional context from documentation would specify the exact interface details]"),
                    ("What are the electrical requirements for {name}?", 
                     "{name} ({value}) typically requires... [Voltage levels and current requirements would be specified in the electrical characteristics section]"),
                ],
            },
            
            EntityType.REGISTER: {
                'factual': [
                    ("What is the address of {name}?", "{value}"),
                    ("What register is located at address {value}?", "{name}"),
                    ("Describe the {name} register.", "The {name} register is located at address {value}."),
                ],
                'configuration': [
                    ("How do I configure {name}?", 
                     "Write the appropriate value to {name} at address {value}. Ensure the device is in configuration mode before writing."),
                    ("What value should be written to {value}?", 
                     "The value written to {value} ({name}) depends on the desired configuration. Consult the register bit definitions for specific values."),
                ],
                'troubleshooting': [
                    ("Why can't I write to {name}?", 
                     "If you cannot write to {name} at {value}, check: 1) Write permissions are enabled, 2) The device is not in protected mode, 3) Clock is enabled for this peripheral, 4) Address {value} is correctly accessed."),
                    ("The {name} register is not updating, what should I check?", 
                     "For {name} at {value}: Verify the register is not write-protected, check if a specific sequence is required before writing, ensure proper timing requirements are met."),
                ],
            },
            
            EntityType.VOLTAGE: {
                'factual': [
                    ("What is the {name}?", "{value}{unit}"),
                    ("What voltage is required for {name}?", "{value}{unit}"),
                    ("Specify the voltage level for {name}.", "The {name} is {value}{unit}."),
                ],
                'tolerance': [
                    ("What is the tolerance for {name}?", 
                     "The {name} of {value}{unit} has a tolerance of {tolerance}."),
                    ("What is the acceptable voltage range for {name}?", 
                     "The acceptable range for {name} is {value}{unit} {tolerance}."),
                ],
                'safety': [
                    ("What happens if {name} exceeds specifications?", 
                     "Exceeding {value}{unit} for {name} may result in permanent damage to the component. Always ensure voltage levels remain within specified tolerances."),
                    ("Is {value}{unit} safe for continuous operation?", 
                     "Yes, {value}{unit} is within the specified operating range for {name}. Ensure proper thermal management for continuous operation."),
                ],
            },
            
            EntityType.TIMING: {
                'factual': [
                    ("What is the {name}?", "{value}{unit}"),
                    ("How long is the {name}?", "{value}{unit}"),
                    ("Specify the timing requirement for {name}.", "The {name} is {value}{unit}."),
                ],
                'calculation': [
                    ("If the {name} is {value}{unit}, what is the maximum frequency?", 
                     "With a {name} of {value}{unit}, the maximum frequency is approximately " + 
                     "{freq_calc} Hz."),
                    ("How many clock cycles are needed for {name}?", 
                     "At a given clock frequency f, the number of cycles for {name} ({value}{unit}) is: cycles = f × {value}{unit}."),
                ],
                'design': [
                    ("How does {name} affect system design?", 
                     "The {name} of {value}{unit} must be considered when designing the system timing. Ensure adequate margin for temperature and voltage variations."),
                    ("What factors affect the {name}?", 
                     "The {name} ({value}{unit}) can be affected by temperature, supply voltage, load capacitance, and process variations."),
                ],
            },
            
            EntityType.BITFIELD: {
                'factual': [
                    ("What is the function of {name}?", "{value}"),
                    ("What does {name} control?", "{name} controls {value}."),
                    ("Describe {name}.", "{name} is used for {value}."),
                ],
                'configuration': [
                    ("How do I enable {value}?", 
                     "To enable {value}, set {name} to 1."),
                    ("What bit configuration is needed for {value}?", 
                     "For {value}, configure {name} appropriately. Typically, setting the bit to 1 enables the function."),
                ],
                'register_context': [
                    ("In which register is {name} located?", 
                     "{name} is located in the control register. Check the register map for the specific address."),
                    ("What other bits are in the same register as {name}?", 
                     "The register containing {name} also includes other control bits. Consult the register definition for complete bit field information."),
                ],
            },
        }
        
        # Add templates for procedures and error codes
        self.templates[EntityType.PROCEDURE_STEP] = {
            'factual': [
                ("What is {name} in the configuration procedure?", "{value}"),
                ("Describe {name}.", "{value}"),
                ("What action is required for {name}?", "{value}"),
            ],
            'sequence': [
                ("What comes after {name}?", 
                 "After {name}, proceed to the next step in the sequence. Ensure {value} is completed successfully before continuing."),
                ("Can {name} be skipped?", 
                 "No, {name} is required. {value} must be completed for proper operation."),
            ],
        }
        
        self.templates[EntityType.ERROR_CODE] = {
            'factual': [
                ("What does {name} mean?", "{value}"),
                ("What error is indicated by {name}?", "{name} indicates: {value}"),
                ("Describe {name}.", "{name}: {value}"),
            ],
            'troubleshooting': [
                ("How do I resolve {name}?", 
                 "To resolve {name} ({value}), check the conditions that trigger this error and ensure all requirements are met."),
                ("What causes {name}?", 
                 "{name} occurs when: {value}. Check system configuration and operating conditions."),
            ],
        }
    
    def generate_qa_pairs(self, entities: List[TechnicalEntity], 
                         complexity_distribution: Dict[str, float] = None) -> List[Dict]:
        """Generate Q&A pairs from a list of entities"""
        if not complexity_distribution:
            complexity_distribution = {
                'basic': 0.4,
                'intermediate': 0.4,
                'advanced': 0.2
            }
        
        qa_pairs = []
        
        for entity in entities:
            # Generate multiple Q&A pairs per entity
            entity_qa_pairs = self._generate_entity_qa_pairs(entity)
            qa_pairs.extend(entity_qa_pairs)
        
        # Convert to training format
        training_data = []
        for qa in qa_pairs:
            training_data.append({
                "messages": [
                    {"role": "user", "content": qa.question},
                    {"role": "assistant", "content": qa.answer}
                ]
            })
        
        return training_data
    
    def _generate_entity_qa_pairs(self, entity: TechnicalEntity) -> List[QAPair]:
        """Generate multiple Q&A pairs from a single entity"""
        qa_pairs = []
        
        # Get templates for this entity type
        entity_templates = self.templates.get(entity.entity_type, {})
        
        # Generate Q&A for each category
        for category, templates in entity_templates.items():
            for q_template, a_template in templates:
                try:
                    # Format the templates with entity data
                    question = self._format_template(q_template, entity)
                    answer = self._format_template(a_template, entity)
                    
                    # Determine difficulty based on category
                    difficulty = self._determine_difficulty(category, entity)
                    
                    qa_pairs.append(QAPair(
                        question=question,
                        answer=answer,
                        category=category,
                        difficulty=difficulty,
                        metadata=entity.metadata
                    ))
                except Exception as e:
                    # Skip malformed templates
                    continue
        
        return qa_pairs
    
    def _format_template(self, template: str, entity: TechnicalEntity) -> str:
        """Format a template with entity data"""
        # Basic replacements
        result = template.replace('{name}', entity.name)
        result = result.replace('{value}', entity.value or 'N/A')
        result = result.replace('{unit}', entity.unit or '')
        
        # Handle metadata replacements
        if entity.metadata:
            for key, value in entity.metadata.items():
                result = result.replace(f'{{{key}}}', str(value))
        
        # Special calculations
        if '{freq_calc}' in result and entity.entity_type == EntityType.TIMING:
            try:
                # Convert timing to frequency (simplified)
                timing_value = float(entity.value)
                if entity.unit == 'ns':
                    freq = 1e9 / timing_value
                elif entity.unit == 'us' or entity.unit == 'μs':
                    freq = 1e6 / timing_value
                elif entity.unit == 'ms':
                    freq = 1e3 / timing_value
                else:  # seconds
                    freq = 1 / timing_value
                
                result = result.replace('{freq_calc}', f'{freq:.2e}')
            except:
                result = result.replace('{freq_calc}', 'calculated frequency')
        
        return result.strip()
    
    def _determine_difficulty(self, category: str, entity: TechnicalEntity) -> str:
        """Determine question difficulty based on category and entity complexity"""
        # Basic factual questions
        if category in ['factual', 'reverse_lookup']:
            return 'basic'
        
        # Questions requiring understanding
        elif category in ['configuration', 'tolerance', 'sequence']:
            return 'intermediate'
        
        # Complex troubleshooting and design questions
        elif category in ['troubleshooting', 'integration', 'design', 'calculation']:
            return 'advanced'
        
        # Default
        return 'intermediate'
    
    def generate_table_qa_pairs(self, table: Table) -> List[Dict]:
        """Generate Q&A pairs from table data"""
        qa_pairs = []
        
        # Generate questions about the entire table
        table_questions = self._generate_table_level_questions(table)
        qa_pairs.extend(table_questions)
        
        # Generate questions for each row
        for row_idx, row in enumerate(table.rows):
            row_questions = self._generate_row_questions(table, row_idx, row)
            qa_pairs.extend(row_questions)
        
        # Convert to training format
        training_data = []
        for qa in qa_pairs:
            training_data.append({
                "messages": [
                    {"role": "user", "content": qa.question},
                    {"role": "assistant", "content": qa.answer}
                ]
            })
        
        return training_data
    
    def _generate_table_level_questions(self, table: Table) -> List[QAPair]:
        """Generate questions about the entire table"""
        qa_pairs = []
        
        # Count-based questions
        if table.table_type == 'pin_table':
            qa_pairs.append(QAPair(
                question=f"How many pins are defined in the pin configuration?",
                answer=f"There are {len(table.rows)} pins defined in the configuration.",
                category='factual',
                difficulty='basic'
            ))
        
        # Summary questions
        if table.headers and len(table.headers) > 1:
            qa_pairs.append(QAPair(
                question=f"What information is provided in the {table.table_type.replace('_', ' ')}?",
                answer=f"The table provides the following information: {', '.join(table.headers)}.",
                category='factual',
                difficulty='basic'
            ))
        
        return qa_pairs
    
    def _generate_row_questions(self, table: Table, row_idx: int, row: List[str]) -> List[QAPair]:
        """Generate questions for a specific table row"""
        qa_pairs = []
        
        # Create a mapping of headers to values
        if len(table.headers) != len(row):
            return qa_pairs  # Skip malformed rows
        
        row_data = dict(zip(table.headers, row))
        
        # Generate specific questions based on table type
        if table.table_type == 'pin_table' and 'Pin' in row_data and 'Function' in row_data:
            pin = row_data['Pin']
            function = row_data['Function']
            
            qa_pairs.extend([
                QAPair(
                    question=f"What is the function of Pin {pin}?",
                    answer=function,
                    category='factual',
                    difficulty='basic'
                ),
                QAPair(
                    question=f"Which pin is assigned for {function}?",
                    answer=f"Pin {pin}",
                    category='reverse_lookup',
                    difficulty='basic'
                )
            ])
        
        elif table.table_type == 'register_table' and 'Address' in row_data:
            address = row_data['Address']
            name = row_data.get('Name', 'Register')
            description = row_data.get('Description', '')
            
            qa_pairs.append(QAPair(
                question=f"What is located at address {address}?",
                answer=f"{name}: {description}" if description else name,
                category='factual',
                difficulty='basic'
            ))
        
        return qa_pairs
    
    def generate_contextual_qa_pairs(self, entities: List[TechnicalEntity], 
                                   context_window: int = 3) -> List[Dict]:
        """Generate Q&A pairs that require understanding context from multiple entities"""
        qa_pairs = []
        
        # Group entities by type and proximity
        entity_groups = self._group_related_entities(entities, context_window)
        
        for group in entity_groups:
            if len(group) > 1:
                # Generate comparison questions
                comparison_qa = self._generate_comparison_questions(group)
                qa_pairs.extend(comparison_qa)
                
                # Generate relationship questions
                relationship_qa = self._generate_relationship_questions(group)
                qa_pairs.extend(relationship_qa)
        
        # Convert to training format
        training_data = []
        for qa in qa_pairs:
            training_data.append({
                "messages": [
                    {"role": "user", "content": qa.question},
                    {"role": "assistant", "content": qa.answer}
                ]
            })
        
        return training_data
    
    def _group_related_entities(self, entities: List[TechnicalEntity], 
                              window: int) -> List[List[TechnicalEntity]]:
        """Group entities that are related or appear close together"""
        groups = []
        
        # Simple proximity-based grouping
        for i in range(0, len(entities), window):
            group = entities[i:i+window]
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _generate_comparison_questions(self, group: List[TechnicalEntity]) -> List[QAPair]:
        """Generate questions comparing multiple entities"""
        qa_pairs = []
        
        # Compare entities of the same type
        same_type_entities = {}
        for entity in group:
            if entity.entity_type not in same_type_entities:
                same_type_entities[entity.entity_type] = []
            same_type_entities[entity.entity_type].append(entity)
        
        for entity_type, entities in same_type_entities.items():
            if len(entities) > 1 and entity_type == EntityType.VOLTAGE:
                # Voltage comparison
                voltages = [(e.name, float(e.value)) for e in entities if e.value]
                if len(voltages) > 1:
                    min_v = min(voltages, key=lambda x: x[1])
                    max_v = max(voltages, key=lambda x: x[1])
                    
                    qa_pairs.append(QAPair(
                        question=f"What is the difference between {min_v[0]} and {max_v[0]}?",
                        answer=f"{min_v[0]} is {min_v[1]}V while {max_v[0]} is {max_v[1]}V, a difference of {max_v[1]-min_v[1]:.1f}V.",
                        category='comparison',
                        difficulty='intermediate'
                    ))
        
        return qa_pairs
    
    def _generate_relationship_questions(self, group: List[TechnicalEntity]) -> List[QAPair]:
        """Generate questions about relationships between entities"""
        qa_pairs = []
        
        # Look for pin-voltage relationships
        pins = [e for e in group if e.entity_type == EntityType.PIN]
        voltages = [e for e in group if e.entity_type == EntityType.VOLTAGE]
        
        if pins and voltages:
            for pin in pins:
                if 'power' in pin.value.lower() or 'vdd' in pin.value.lower():
                    for voltage in voltages:
                        qa_pairs.append(QAPair(
                            question=f"What voltage should be applied to {pin.name}?",
                            answer=f"{pin.name} ({pin.value}) requires {voltage.value}{voltage.unit}.",
                            category='integration',
                            difficulty='intermediate'
                        ))
                        break
        
        return qa_pairs
