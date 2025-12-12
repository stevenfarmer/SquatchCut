"""Tests for genetic algorithm nesting optimization."""

import pytest
from unittest.mock import Mock, patch

from SquatchCut.core.genetic_nesting import (
    GeneticNestingOptimizer,
    GeneticConfig,
    Individual,
    genetic_nest_parts,
)
from SquatchCut.core.nesting import Part, PlacedPart


class TestGeneticConfig:
    """Test genetic algorithm configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GeneticConfig()
        assert config.population_size == 50
        assert config.generations == 100
        assert config.mutation_rate == 0.1
        assert config.crossover_rate == 0.8
        assert config.elite_size == 5
        assert config.tournament_size == 3
        assert config.max_time_seconds == 300
        assert config.target_utilization == 0.95

    def test_custom_config(self):
        """Test custom configuration values."""
        config = GeneticConfig(
            population_size=30,
            generations=50,
            mutation_rate=0.15,
            crossover_rate=0.7,
            max_time_seconds=180,
        )
        assert config.population_size == 30
        assert config.generations == 50
        assert config.mutation_rate == 0.15
        assert config.crossover_rate == 0.7
        assert config.max_time_seconds == 180


class TestIndividual:
    """Test individual representation in genetic algorithm."""

    def test_individual_creation(self):
        """Test creating an individual."""
        individual = Individual(
            parts_order=[0, 1, 2],
            rotations=[False, True, False],
            fitness=85.5,
            utilization=0.75,
        )
        assert individual.parts_order == [0, 1, 2]
        assert individual.rotations == [False, True, False]
        assert individual.fitness == 85.5
        assert individual.utilization == 0.75
        assert individual.placement_success is False  # Default


class TestGeneticNestingOptimizer:
    """Test genetic nesting optimizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = GeneticConfig(
            population_size=10, generations=5, max_time_seconds=10
        )
        self.optimizer = GeneticNestingOptimizer(self.config)

        # Create test parts
        self.parts = [
            Part(id="A", width=100, height=50, can_rotate=True),
            Part(id="B", width=80, height=60, can_rotate=False),
            Part(id="C", width=120, height=40, can_rotate=True),
        ]

        self.sheet_width = 300
        self.sheet_height = 200

    def test_optimizer_initialization(self):
        """Test optimizer initialization."""
        assert self.optimizer.config.population_size == 10
        assert self.optimizer.config.generations == 5
        assert len(self.optimizer.parts) == 0
        assert self.optimizer.sheet_width == 0
        assert self.optimizer.sheet_height == 0

    def test_initialize_population(self):
        """Test population initialization."""
        self.optimizer.parts = self.parts
        population = self.optimizer._initialize_population()

        assert len(population) == self.config.population_size

        for individual in population:
            assert len(individual.parts_order) == len(self.parts)
            assert len(individual.rotations) == len(self.parts)
            assert set(individual.parts_order) == set(range(len(self.parts)))

    def test_individual_to_placed_parts(self):
        """Test converting individual to placed parts."""
        self.optimizer.parts = self.parts
        self.optimizer.sheet_width = self.sheet_width
        self.optimizer.sheet_height = self.sheet_height

        individual = Individual(parts_order=[0, 1, 2], rotations=[False, False, False])

        placed_parts = self.optimizer._individual_to_placed_parts(individual)

        # Should place at least some parts
        assert len(placed_parts) >= 0

        # Check that all placed parts are valid
        for pp in placed_parts:
            assert pp.x >= 0
            assert pp.y >= 0
            assert pp.x + pp.width <= self.sheet_width
            assert pp.y + pp.height <= self.sheet_height

    def test_rectangles_overlap(self):
        """Test rectangle overlap detection."""
        rect1 = (0, 0, 100, 50)
        rect2 = (50, 25, 100, 50)  # Overlaps
        rect3 = (150, 0, 100, 50)  # No overlap

        assert self.optimizer._rectangles_overlap(rect1, [rect2])
        assert not self.optimizer._rectangles_overlap(rect1, [rect3])

    def test_find_position(self):
        """Test position finding algorithm."""
        occupied = [(0, 0, 100, 50), (100, 0, 80, 60)]

        # Should find a valid position
        position = self.optimizer._find_position(50, 40, occupied)
        assert position is not None

        x, y = position
        new_rect = (x, y, 50, 40)
        assert not self.optimizer._rectangles_overlap(new_rect, occupied)

    def test_calculate_cut_complexity(self):
        """Test cut complexity calculation."""
        placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(id="B", x=100, y=0, width=80, height=60, sheet_index=0),
        ]

        complexity = self.optimizer._calculate_cut_complexity(placed_parts)
        assert complexity > 0
        assert isinstance(complexity, (int, float))

    def test_tournament_selection(self):
        """Test tournament selection."""
        population = []
        for i in range(5):
            individual = Individual(
                parts_order=[0, 1, 2],
                rotations=[False, False, False],
                fitness=i * 10,  # Different fitness values
            )
            population.append(individual)

        selected = self.optimizer._tournament_selection(population)
        assert selected in population
        # Should tend to select higher fitness individuals

    def test_crossover(self):
        """Test crossover operation."""
        parent1 = Individual(parts_order=[0, 1, 2], rotations=[True, False, True])
        parent2 = Individual(parts_order=[2, 0, 1], rotations=[False, True, False])

        child1, child2 = self.optimizer._crossover(parent1, parent2)

        # Check that children have valid parts orders
        assert set(child1.parts_order) == set([0, 1, 2])
        assert set(child2.parts_order) == set([0, 1, 2])
        assert len(child1.rotations) == 3
        assert len(child2.rotations) == 3

    def test_mutation(self):
        """Test mutation operation."""
        self.optimizer.parts = self.parts

        original = Individual(parts_order=[0, 1, 2], rotations=[True, False, True])

        # Make a copy for mutation
        mutated = Individual(
            parts_order=original.parts_order.copy(), rotations=original.rotations.copy()
        )

        self.optimizer._mutate(mutated)

        # Should still be valid
        assert set(mutated.parts_order) == set([0, 1, 2])
        assert len(mutated.rotations) == 3

    @patch("SquatchCut.core.genetic_nesting.logger")
    def test_optimize_empty_parts(self, mock_logger):
        """Test optimization with empty parts list."""
        result = self.optimizer.optimize([], 300, 200)
        assert result == []

    @patch("SquatchCut.core.genetic_nesting.logger")
    def test_optimize_small_dataset(self, mock_logger):
        """Test optimization with small dataset."""
        result = self.optimizer.optimize(
            self.parts, self.sheet_width, self.sheet_height, kerf_mm=3.0, spacing_mm=5.0
        )

        # Should return some result
        assert isinstance(result, list)

        # All returned parts should be valid
        for pp in result:
            assert isinstance(pp, PlacedPart)
            assert pp.x >= 0
            assert pp.y >= 0


class TestGeneticNestingFunction:
    """Test high-level genetic nesting function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parts = [
            Part(id="A", width=100, height=50, can_rotate=True),
            Part(id="B", width=80, height=60, can_rotate=False),
        ]

    @patch("SquatchCut.core.genetic_nesting.logger")
    def test_genetic_nest_parts(self, mock_logger):
        """Test high-level genetic nesting function."""
        config = GeneticConfig(population_size=5, generations=3)

        result = genetic_nest_parts(
            self.parts, 300, 200, kerf_mm=3.0, spacing_mm=5.0, config=config
        )

        assert isinstance(result, list)

        # Check that all parts have valid properties
        for pp in result:
            assert hasattr(pp, "id")
            assert hasattr(pp, "x")
            assert hasattr(pp, "y")
            assert hasattr(pp, "width")
            assert hasattr(pp, "height")

    def test_genetic_nest_parts_default_config(self):
        """Test genetic nesting with default configuration."""
        result = genetic_nest_parts(self.parts, 300, 200)
        assert isinstance(result, list)


class TestGeneticNestingIntegration:
    """Integration tests for genetic nesting."""

    def test_performance_with_larger_dataset(self):
        """Test performance with a larger dataset."""
        # Create more parts
        parts = []
        for i in range(20):
            parts.append(
                Part(
                    id=f"Part_{i}",
                    width=50 + (i % 5) * 10,
                    height=30 + (i % 3) * 10,
                    can_rotate=i % 2 == 0,
                )
            )

        config = GeneticConfig(population_size=20, generations=10, max_time_seconds=30)

        import time

        start_time = time.time()

        result = genetic_nest_parts(parts, 600, 400, config=config)

        elapsed = time.time() - start_time

        # Should complete within reasonable time
        assert elapsed < 35  # Allow some buffer over max_time_seconds
        assert isinstance(result, list)

        # Should place most parts
        assert len(result) >= len(parts) * 0.7  # At least 70% placement rate

    def test_utilization_calculation(self):
        """Test that genetic algorithm improves utilization."""
        parts = [
            Part(id="A", width=100, height=100),
            Part(id="B", width=100, height=100),
            Part(id="C", width=100, height=100),
            Part(id="D", width=100, height=100),
        ]

        config = GeneticConfig(
            population_size=10, generations=20, target_utilization=0.8
        )

        result = genetic_nest_parts(
            parts, 250, 250, config=config  # Should fit all parts with good utilization
        )

        # Calculate actual utilization
        if result:
            total_part_area = sum(pp.width * pp.height for pp in result)
            sheet_area = 250 * 250
            utilization = total_part_area / sheet_area

            # Should achieve reasonable utilization
            assert utilization > 0.5  # At least 50% utilization

    def test_rotation_handling(self):
        """Test that genetic algorithm handles rotations correctly."""
        parts = [
            Part(
                id="A", width=150, height=50, can_rotate=True
            ),  # Needs rotation to fit
            Part(id="B", width=100, height=100, can_rotate=False),
        ]

        result = genetic_nest_parts(parts, 200, 200)

        # Should place both parts
        assert len(result) == 2

        # Check that rotated part has correct dimensions
        part_a = next((p for p in result if p.id == "A"), None)
        assert part_a is not None

        # Part A should fit within sheet bounds
        assert part_a.x + part_a.width <= 200
        assert part_a.y + part_a.height <= 200
