import yaml
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ModuleCharacteristics:
    """Container for module characteristic data"""
    module_title: str
    program: str
    year: int
    difficulty_level: float
    social_requirements: float
    creativity_requirements: float
    practical_theoretical_balance: float
    stress_level: float
    group_work_intensity: float
    independent_study_requirement: float
    assessment_type: str
    description: str

@dataclass
class ModuleImpact:
    """Container for calculated module impact on student behavior"""
    attendance_modifier: float
    performance_modifier: float
    stress_modifier: float
    engagement_modifier: float
    dropout_risk_modifier: float

class ModuleCharacteristicsSystem:
    """
    Module characteristics system for Stonegrove University.
    Manages module attributes and calculates their impact on student behavior.
    """
    
    def __init__(self, config_file: str = "config/module_characteristics.yaml"):
        """Initialize the module characteristics system"""
        self.config_file = config_file
        self.module_data = self._load_module_data()
        self.settings = self.module_data.get('settings', {})
        
    def _load_module_data(self) -> Dict:
        """Load module characteristics from YAML configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Module characteristics file not found: {self.config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing module characteristics YAML: {e}")
    
    def get_module_characteristics(self, module_title: str) -> Optional[ModuleCharacteristics]:
        """Get characteristics for a specific module"""
        modules = self.module_data.get('modules', {})
        if module_title not in modules:
            return None
        
        module_info = modules[module_title]
        return ModuleCharacteristics(
            module_title=module_title,
            program=module_info['program'],
            year=module_info['year'],
            difficulty_level=module_info['difficulty_level'],
            social_requirements=module_info['social_requirements'],
            creativity_requirements=module_info['creativity_requirements'],
            practical_theoretical_balance=module_info['practical_theoretical_balance'],
            stress_level=module_info['stress_level'],
            group_work_intensity=module_info['group_work_intensity'],
            independent_study_requirement=module_info['independent_study_requirement'],
            assessment_type=module_info['assessment_type'],
            description=module_info['description']
        )
    
    def get_modules_by_program(self, program: str) -> List[ModuleCharacteristics]:
        """Get all modules for a specific program"""
        modules = self.module_data.get('modules', {})
        program_modules = []
        
        for module_title, module_info in modules.items():
            if module_info['program'] == program:
                program_modules.append(self.get_module_characteristics(module_title))
        
        return program_modules
    
    def get_modules_by_year(self, year: int) -> List[ModuleCharacteristics]:
        """Get all modules for a specific year"""
        modules = self.module_data.get('modules', {})
        year_modules = []
        
        for module_title, module_info in modules.items():
            if module_info['year'] == year:
                year_modules.append(self.get_module_characteristics(module_title))
        
        return year_modules
    
    def calculate_module_impact(self, module_title: str, student_personality: Dict) -> ModuleImpact:
        """
        Calculate how a module will impact a specific student's behavior
        based on their personality and the module characteristics
        """
        module = self.get_module_characteristics(module_title)
        if not module:
            raise ValueError(f"Module '{module_title}' not found")
        
        # Base impact calculations
        attendance_modifier = self._calculate_attendance_impact(module, student_personality)
        performance_modifier = self._calculate_performance_impact(module, student_personality)
        stress_modifier = self._calculate_stress_impact(module, student_personality)
        engagement_modifier = self._calculate_engagement_impact(module, student_personality)
        dropout_risk_modifier = self._calculate_dropout_risk_impact(module, student_personality)
        
        return ModuleImpact(
            attendance_modifier=attendance_modifier,
            performance_modifier=performance_modifier,
            stress_modifier=stress_modifier,
            engagement_modifier=engagement_modifier,
            dropout_risk_modifier=dropout_risk_modifier
        )
    
    def _calculate_attendance_impact(self, module: ModuleCharacteristics, personality: Dict) -> float:
        """Calculate impact on attendance based on module characteristics and personality"""
        base_impact = 0.0
        
        # Difficulty impact (negative for high difficulty)
        difficulty_impact = -0.3 * module.difficulty_level
        base_impact += difficulty_impact
        
        # Social requirements impact (positive for extraverts, negative for introverts)
        extraversion = personality.get('extraversion', 0.5)
        social_impact = (extraversion - 0.5) * module.social_requirements * 0.4
        base_impact += social_impact
        
        # Practical balance impact (positive for hands-on learners)
        practical_impact = module.practical_theoretical_balance * 0.2
        base_impact += practical_impact
        
        # Stress impact (negative for high stress)
        stress_impact = -0.2 * module.stress_level
        base_impact += stress_impact
        
        # Independent study impact (negative for those who prefer structure)
        conscientiousness = personality.get('conscientiousness', 0.5)
        independent_impact = (conscientiousness - 0.5) * module.independent_study_requirement * 0.3
        base_impact += independent_impact
        
        return np.clip(base_impact, -1.0, 1.0)
    
    def _calculate_performance_impact(self, module: ModuleCharacteristics, personality: Dict) -> float:
        """Calculate impact on performance based on module characteristics and personality"""
        base_impact = 0.0
        
        # Difficulty interaction with conscientiousness
        conscientiousness = personality.get('conscientiousness', 0.5)
        difficulty_performance = (conscientiousness - 0.5) * module.difficulty_level * 0.4
        base_impact += difficulty_performance
        
        # Creativity requirements interaction with openness
        openness = personality.get('openness', 0.5)
        creativity_performance = (openness - 0.5) * module.creativity_requirements * 0.5
        base_impact += creativity_performance
        
        # Social requirements interaction with extraversion
        extraversion = personality.get('extraversion', 0.5)
        social_performance = (extraversion - 0.5) * module.social_requirements * 0.3
        base_impact += social_performance
        
        # Practical balance interaction with academic curiosity
        academic_curiosity = personality.get('academic_curiosity', 0.5)
        practical_performance = (academic_curiosity - 0.5) * module.practical_theoretical_balance * 0.3
        base_impact += practical_performance
        
        return np.clip(base_impact, -1.0, 1.0)
    
    def _calculate_stress_impact(self, module: ModuleCharacteristics, personality: Dict) -> float:
        """Calculate impact on stress levels"""
        base_stress = module.stress_level
        
        # Neuroticism amplifies stress
        neuroticism = personality.get('neuroticism', 0.5)
        stress_amplification = neuroticism * 0.3
        base_stress += stress_amplification
        
        # Resilience reduces stress
        resilience = personality.get('resilience', 0.5)
        stress_reduction = (1.0 - resilience) * 0.2
        base_stress += stress_reduction
        
        # Social anxiety amplifies stress in high-social modules
        social_anxiety = personality.get('social_anxiety', 0.5)
        social_stress = social_anxiety * module.social_requirements * 0.3
        base_stress += social_stress
        
        return np.clip(base_stress, 0.0, 1.0)
    
    def _calculate_engagement_impact(self, module: ModuleCharacteristics, personality: Dict) -> float:
        """Calculate impact on engagement levels"""
        base_engagement = 0.5
        
        # Creativity requirements boost engagement for creative personalities
        openness = personality.get('openness', 0.5)
        creativity_engagement = openness * module.creativity_requirements * 0.4
        base_engagement += creativity_engagement
        
        # Social requirements boost engagement for extraverts
        extraversion = personality.get('extraversion', 0.5)
        social_engagement = extraversion * module.social_requirements * 0.3
        base_engagement += social_engagement
        
        # Practical balance boosts engagement for hands-on learners
        practical_engagement = module.practical_theoretical_balance * 0.2
        base_engagement += practical_engagement
        
        # Difficulty can boost engagement for high-achievers
        perfectionism = personality.get('perfectionism', 0.5)
        difficulty_engagement = perfectionism * module.difficulty_level * 0.2
        base_engagement += difficulty_engagement
        
        return np.clip(base_engagement, 0.0, 1.0)
    
    def _calculate_dropout_risk_impact(self, module: ModuleCharacteristics, personality: Dict) -> float:
        """Calculate impact on dropout risk"""
        base_risk = module.difficulty_level * 0.3 + module.stress_level * 0.3
        
        # High conscientiousness reduces dropout risk
        conscientiousness = personality.get('conscientiousness', 0.5)
        conscientiousness_reduction = (1.0 - conscientiousness) * 0.2
        base_risk += conscientiousness_reduction
        
        # High neuroticism increases dropout risk
        neuroticism = personality.get('neuroticism', 0.5)
        neuroticism_risk = neuroticism * 0.2
        base_risk += neuroticism_risk
        
        # Low resilience increases dropout risk
        resilience = personality.get('resilience', 0.5)
        resilience_risk = (1.0 - resilience) * 0.2
        base_risk += resilience_risk
        
        return np.clip(base_risk, 0.0, 1.0)
    
    def get_difficulty_level_description(self, difficulty: float) -> str:
        """Get human-readable description of difficulty level"""
        levels = self.settings.get('difficulty_levels', {})
        
        for level_name, (min_val, max_val) in levels.items():
            if min_val <= difficulty < max_val:
                return level_name.replace('_', ' ').title()
        
        return "Unknown"
    
    def get_social_requirement_description(self, social_req: float) -> str:
        """Get human-readable description of social requirements"""
        levels = self.settings.get('social_requirement_levels', {})
        
        for level_name, (min_val, max_val) in levels.items():
            if min_val <= social_req < max_val:
                return level_name.replace('_', ' ').title()
        
        return "Unknown"
    
    def get_creativity_requirement_description(self, creativity_req: float) -> str:
        """Get human-readable description of creativity requirements"""
        levels = self.settings.get('creativity_requirement_levels', {})
        
        for level_name, (min_val, max_val) in levels.items():
            if min_val <= creativity_req < max_val:
                return level_name.replace('_', ' ').title()
        
        return "Unknown"
    
    def get_available_modules(self) -> List[str]:
        """Get list of all available module titles"""
        return list(self.module_data.get('modules', {}).keys())
    
    def get_available_programs(self) -> List[str]:
        """Get list of all available programs"""
        modules = self.module_data.get('modules', {})
        programs = set()
        
        for module_info in modules.values():
            programs.add(module_info['program'])
        
        return sorted(list(programs))
    
    def validate_module_data(self) -> bool:
        """Validate that all module data is properly configured"""
        try:
            modules = self.module_data.get('modules', {})
            
            for module_title, module_info in modules.items():
                required_fields = [
                    'program', 'year', 'difficulty_level', 'social_requirements',
                    'creativity_requirements', 'practical_theoretical_balance',
                    'stress_level', 'group_work_intensity', 'independent_study_requirement',
                    'assessment_type', 'description'
                ]
                
                for field in required_fields:
                    if field not in module_info:
                        print(f"Warning: Module '{module_title}' missing field '{field}'")
                        return False
                
                # Validate numeric ranges
                numeric_fields = [
                    'difficulty_level', 'social_requirements', 'creativity_requirements',
                    'practical_theoretical_balance', 'stress_level', 'group_work_intensity',
                    'independent_study_requirement'
                ]
                
                for field in numeric_fields:
                    value = module_info[field]
                    if not isinstance(value, (int, float)) or value < 0 or value > 1:
                        print(f"Warning: Module '{module_title}' has invalid {field}: {value}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"Error validating module data: {e}")
            return False

def main():
    """Test the module characteristics system"""
    print("📚 Stonegrove University Module Characteristics System")
    print("=" * 60)
    
    # Initialize system
    system = ModuleCharacteristicsSystem()
    
    # Validate configuration
    if not system.validate_module_data():
        print("❌ Module data validation failed!")
        return
    
    print("✅ Module data validation passed!")
    print(f"📚 Available modules: {len(system.get_available_modules())}")
    print(f"🎓 Available programs: {len(system.get_available_programs())}")
    print()
    
    # Test module characteristics retrieval
    print("🔍 Testing module characteristics retrieval:")
    print("-" * 60)
    
    test_modules = [
        "Introduction to Cooperative Crafting",
        "Power Dynamics in Traditional Societies",
        "Introduction to Transdisciplinary Methods"
    ]
    
    for module_title in test_modules:
        module = system.get_module_characteristics(module_title)
        if module:
            print(f"\n📖 {module_title}:")
            print(f"   Program: {module.program}")
            print(f"   Year: {module.year}")
            print(f"   Difficulty: {module.difficulty_level:.2f} ({system.get_difficulty_level_description(module.difficulty_level)})")
            print(f"   Social Requirements: {module.social_requirements:.2f} ({system.get_social_requirement_description(module.social_requirements)})")
            print(f"   Creativity Requirements: {module.creativity_requirements:.2f} ({system.get_creativity_requirement_description(module.creativity_requirements)})")
            print(f"   Stress Level: {module.stress_level:.2f}")
            print(f"   Assessment Type: {module.assessment_type}")
            print(f"   Description: {module.description}")
    
    # Test impact calculation
    print("\n" + "=" * 60)
    print("🎯 Testing module impact calculation:")
    print("-" * 60)
    
    # Sample student personality
    sample_personality = {
        'openness': 0.7,
        'conscientiousness': 0.6,
        'extraversion': 0.4,
        'agreeableness': 0.8,
        'neuroticism': 0.3,
        'academic_curiosity': 0.8,
        'perfectionism': 0.6,
        'resilience': 0.7,
        'social_anxiety': 0.4
    }
    
    print(f"👤 Sample student personality:")
    for trait, value in sample_personality.items():
        print(f"   {trait}: {value:.2f}")
    
    print(f"\n📊 Module impacts for this student:")
    
    for module_title in test_modules:
        try:
            impact = system.calculate_module_impact(module_title, sample_personality)
            print(f"\n📖 {module_title}:")
            print(f"   Attendance Modifier: {impact.attendance_modifier:+.3f}")
            print(f"   Performance Modifier: {impact.performance_modifier:+.3f}")
            print(f"   Stress Modifier: {impact.stress_modifier:.3f}")
            print(f"   Engagement Modifier: {impact.engagement_modifier:.3f}")
            print(f"   Dropout Risk Modifier: {impact.dropout_risk_modifier:.3f}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test program-specific queries
    print("\n" + "=" * 60)
    print("🎓 Testing program-specific queries:")
    print("-" * 60)
    
    test_program = "Critical Power"
    program_modules = system.get_modules_by_program(test_program)
    print(f"\n📚 Modules in {test_program}:")
    for module in program_modules:
        print(f"   - {module.module_title} (Year {module.year})")
    
    # Test year-specific queries
    print(f"\n📅 Year 1 modules:")
    year1_modules = system.get_modules_by_year(1)
    for module in year1_modules[:5]:  # Show first 5
        print(f"   - {module.module_title} ({module.program})")
    if len(year1_modules) > 5:
        print(f"   ... and {len(year1_modules) - 5} more")
    
    print(f"\n✅ Module characteristics system test completed!")

if __name__ == "__main__":
    main() 