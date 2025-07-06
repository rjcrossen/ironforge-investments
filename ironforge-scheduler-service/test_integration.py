#!/usr/bin/env python3
"""
Test script to verify repository integration with database.py
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from repository.database import db_session, get_session
from repository.recipe_repository import RecipeRepository
from repository.reagent_repository import ReagentRepository
from models.models import Recipe, Reagent


def test_database_connection():
    """Test basic database connection."""
    try:
        with db_session() as session:
            print("✓ Database connection successful")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_repository_initialization():
    """Test repository initialization with session."""
    try:
        with db_session() as session:
            recipe_repo = RecipeRepository(session)
            reagent_repo = ReagentRepository(session)
            print("✓ Repository initialization successful")
            return True
    except Exception as e:
        print(f"✗ Repository initialization failed: {e}")
        return False


def test_model_imports():
    """Test that models can be imported correctly."""
    try:
        # Test that we can access model attributes
        recipe_table = Recipe.__tablename__
        reagent_table = Reagent.__tablename__
        print(f"✓ Model imports successful (tables: {recipe_table}, {reagent_table})")
        return True
    except Exception as e:
        print(f"✗ Model imports failed: {e}")
        return False


def test_repository_methods():
    """Test basic repository method calls."""
    try:
        with db_session() as session:
            recipe_repo = RecipeRepository(session)
            reagent_repo = ReagentRepository(session)
            
            # Test empty batch insert (should not fail)
            recipe_repo.batch_insert([])
            reagent_repo.batch_insert([])
            
            # Test query methods (should return empty results on fresh DB)
            recipes = recipe_repo.get_recipes_by_profession("Alchemy")
            reagents = reagent_repo.get_reagents_by_recipe(12345)
            
            print(f"✓ Repository methods work (found {len(recipes)} recipes, {len(reagents)} reagents)")
            return True
    except Exception as e:
        print(f"✗ Repository methods failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("Testing repository integration with database.py...")
    print("=" * 50)
    
    tests = [
        test_model_imports,
        test_database_connection,
        test_repository_initialization,
        test_repository_methods,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Integration test results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Repositories are properly integrated.")
        return 0
    else:
        print("❌ Some integration tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())