#!/usr/bin/env python3
"""
Configuration Editor for Stonegrove University Population Generator

This script helps you easily modify the distribution percentages in the YAML config files.
"""

import yaml
import os
import sys
from pathlib import Path

def load_yaml_file(filepath):
    """Load a YAML file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML file {filepath}: {e}")
        return None

def save_yaml_file(filepath, data):
    """Save data to a YAML file."""
    try:
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Saved to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error saving file {filepath}: {e}")
        return False

def display_distribution(data, title):
    """Display a distribution with percentages."""
    print(f"\n📊 {title}")
    print("-" * 50)
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"\n  {key}:")
                for subkey, subvalue in value.items():
                    percentage = subvalue * 100
                    print(f"    {subkey}: {percentage:.1f}%")
            else:
                percentage = value * 100
                print(f"  {key}: {percentage:.1f}%")
    else:
        print(f"  {data}")

def edit_simple_distribution(data, title):
    """Edit a simple key-value distribution."""
    print(f"\n✏️  Editing {title}")
    print("-" * 50)
    
    new_data = {}
    total = 0.0
    
    for key, value in data.items():
        percentage = value * 100
        print(f"\nCurrent {key}: {percentage:.1f}%")
        
        while True:
            try:
                new_percentage = input(f"New {key} percentage (or press Enter to keep current): ").strip()
                if new_percentage == "":
                    new_value = value
                else:
                    new_value = float(new_percentage) / 100
                    if new_value < 0 or new_value > 1:
                        print("❌ Percentage must be between 0 and 100")
                        continue
                
                new_data[key] = new_value
                total += new_value
                break
            except ValueError:
                print("❌ Please enter a valid number")
    
    print(f"\n📊 Total: {total:.3f} ({total*100:.1f}%)")
    if abs(total - 1.0) > 0.001:
        print("⚠️  Warning: Total does not equal 100%")
        adjust = input("Would you like to normalize to 100%? (y/n): ").lower()
        if adjust == 'y':
            for key in new_data:
                new_data[key] = new_data[key] / total
            print("✅ Normalized to 100%")
    
    return new_data

def edit_disability_distribution(data, title):
    """Edit disability distribution by species."""
    print(f"\n✏️  Editing {title}")
    print("-" * 50)
    
    new_data = {}
    
    for species, disabilities in data.items():
        print(f"\n🏛️  {species} Disabilities:")
        new_disabilities = {}
        total = 0.0
        
        for disability, value in disabilities.items():
            percentage = value * 100
            print(f"\n  Current {disability}: {percentage:.1f}%")
            
            while True:
                try:
                    new_percentage = input(f"  New {disability} percentage (or press Enter to keep current): ").strip()
                    if new_percentage == "":
                        new_value = value
                    else:
                        new_value = float(new_percentage) / 100
                        if new_value < 0 or new_value > 1:
                            print("  ❌ Percentage must be between 0 and 100")
                            continue
                    
                    new_disabilities[disability] = new_value
                    total += new_value
                    break
                except ValueError:
                    print("  ❌ Please enter a valid number")
        
        print(f"\n  📊 {species} Total: {total:.3f} ({total*100:.1f}%)")
        if abs(total - 1.0) > 0.001:
            print("  ⚠️  Warning: Total does not equal 100%")
            adjust = input("  Would you like to normalize to 100%? (y/n): ").lower()
            if adjust == 'y':
                for disability in new_disabilities:
                    new_disabilities[disability] = new_disabilities[disability] / total
                print("  ✅ Normalized to 100%")
        
        new_data[species] = new_disabilities
    
    return new_data

def main():
    """Main configuration editor function."""
    print("🏛️  Stonegrove University Configuration Editor")
    print("=" * 60)
    
    config_dir = Path("config")
    if not config_dir.exists():
        print("❌ Config directory not found. Please run the population generator first.")
        return
    
    # List available config files
    config_files = list(config_dir.glob("*.yaml"))
    if not config_files:
        print("❌ No YAML config files found in config directory.")
        return
    
    print("\n📁 Available configuration files:")
    for i, file in enumerate(config_files, 1):
        print(f"  {i}. {file.name}")
    
    print(f"  {len(config_files) + 1}. Exit")
    
    while True:
        try:
            choice = input(f"\nSelect a file to edit (1-{len(config_files) + 1}): ").strip()
            choice_num = int(choice)
            
            if choice_num == len(config_files) + 1:
                print("👋 Goodbye!")
                break
            
            if choice_num < 1 or choice_num > len(config_files):
                print("❌ Invalid choice. Please try again.")
                continue
            
            selected_file = config_files[choice_num - 1]
            data = load_yaml_file(selected_file)
            
            if data is None:
                continue
            
            # Display current configuration
            display_distribution(data, f"Current {selected_file.name}")
            
            # Edit based on file type
            if "disability" in selected_file.name:
                new_data = edit_disability_distribution(data, selected_file.name)
            else:
                new_data = edit_simple_distribution(data, selected_file.name)
            
            # Save changes
            save = input(f"\n💾 Save changes to {selected_file.name}? (y/n): ").lower()
            if save == 'y':
                if save_yaml_file(selected_file, new_data):
                    print("✅ Configuration updated successfully!")
                    print("🔄 Run 'python population_generator.py' to generate new population with updated settings.")
                else:
                    print("❌ Failed to save configuration.")
            
            # Ask if user wants to edit another file
            another = input("\n📝 Edit another configuration file? (y/n): ").lower()
            if another != 'y':
                print("👋 Goodbye!")
                break
                
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main() 