"""Genetic algorithm optimization for advanced nesting."""

import random
import time
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from copy import deepcopy

from SquatchCut.core.nesting import Part, PlacedPart
from SquatchCut.core.performance_utils import performance_monitor, ProgressTracker
from SquatchCut.core import logger


@dataclass
class GeneticConfig:
    """Configuration for genetic algorithm nesting."""

    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_size: int = 5
    tournament_size: int = 3
    max_time_seconds: Optional[float] = 300  # 5 minutes max
    target_utilization: float = 0.95  # Stop if we reach 95% utilization


@dataclass
class Individual:
    """Represents one solution in the genetic algorithm."""

    parts_order: List[int]  # Order to place parts
    rotations: List[bool]  # Whether each part is rotated
    fitness: float = 0.0
    utilization: float = 0.0
    cut_complexity: float = 0.0
    placement_success: bool = False


class GeneticNestingOptimizer:
    """Genetic algorithm optimizer for nesting layouts."""

    def __init__(self, config: GeneticConfig = None):
        self.config = config or GeneticConfig()
        self.parts: List[Part] = []
        self.sheet_width: float = 0
        self.sheet_height: float = 0
        self.kerf_mm: float = 0
        self.spacing_mm: float = 0

    def optimize(
        self,
        parts: List[Part],
        sheet_width: float,
        sheet_height: float,
        kerf_mm: float = 0,
        spacing_mm: float = 0,
    ) -> List[PlacedPart]:
        """Run genetic algorithm optimization."""
        self.parts = parts
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.kerf_mm = kerf_mm
        self.spacing_mm = spacing_mm

        if not parts:
            return []

        logger.info(
            f"Starting genetic optimization: {len(parts)} parts, {self.config.generations} generations"
        )

        # Initialize population
        population = self._initialize_population()

        # Track best solution
        best_individual = None
        best_fitness = float("-inf")
        generations_without_improvement = 0

        start_time = time.time()

        with ProgressTracker(
            self.config.generations, "Genetic Optimization"
        ) as tracker:
            for generation in range(self.config.generations):
                # Evaluate fitness for all individuals
                self._evaluate_population(population)

                # Find best individual
                current_best = max(population, key=lambda x: x.fitness)
                if current_best.fitness > best_fitness:
                    best_fitness = current_best.fitness
                    best_individual = deepcopy(current_best)
                    generations_without_improvement = 0

                    logger.debug(
                        f"Generation {generation}: New best fitness {best_fitness:.3f}, "
                        f"utilization {current_best.utilization:.1%}"
                    )
                else:
                    generations_without_improvement += 1

                # Check termination conditions
                if self._should_terminate(
                    best_individual,
                    generation,
                    start_time,
                    generations_without_improvement,
                ):
                    logger.info(f"Terminating optimization at generation {generation}")
                    break

                # Create next generation
                population = self._create_next_generation(population)
                tracker.update(1)

        # Convert best solution to placed parts
        if best_individual and best_individual.placement_success:
            logger.info(
                f"Genetic optimization complete: fitness {best_individual.fitness:.3f}, "
                f"utilization {best_individual.utilization:.1%}"
            )
            return self._individual_to_placed_parts(best_individual)
        else:
            logger.warning("Genetic optimization failed to find valid solution")
            return []

    def _initialize_population(self) -> List[Individual]:
        """Create initial population with diverse solutions."""
        population = []

        for _ in range(self.config.population_size):
            # Random order of parts
            parts_order = list(range(len(self.parts)))
            random.shuffle(parts_order)

            # Random rotations (only for parts that can rotate)
            rotations = []
            for i in range(len(self.parts)):
                part = self.parts[i]
                can_rotate = getattr(part, "can_rotate", False)
                rotations.append(can_rotate and random.random() < 0.5)

            individual = Individual(parts_order=parts_order, rotations=rotations)
            population.append(individual)

        # Add some heuristic-based individuals
        self._add_heuristic_individuals(population)

        return population[: self.config.population_size]

    def _add_heuristic_individuals(self, population: List[Individual]) -> None:
        """Add individuals based on common heuristics."""
        if len(population) >= self.config.population_size:
            return

        # Sort by area (largest first)
        area_sorted = sorted(
            range(len(self.parts)),
            key=lambda i: self.parts[i].width * self.parts[i].height,
            reverse=True,
        )

        # Sort by longest side first
        longest_side_sorted = sorted(
            range(len(self.parts)),
            key=lambda i: max(self.parts[i].width, self.parts[i].height),
            reverse=True,
        )

        # Add heuristic individuals
        heuristics = [area_sorted, longest_side_sorted]
        for heuristic_order in heuristics:
            if len(population) >= self.config.population_size:
                break

            rotations = [False] * len(self.parts)  # Start with no rotations
            individual = Individual(parts_order=heuristic_order, rotations=rotations)
            population.append(individual)

    def _evaluate_population(self, population: List[Individual]) -> None:
        """Evaluate fitness for all individuals in population."""
        for individual in population:
            if individual.fitness == 0.0:  # Not yet evaluated
                self._evaluate_individual(individual)

    def _evaluate_individual(self, individual: Individual) -> None:
        """Evaluate fitness of a single individual."""
        try:
            placed_parts = self._individual_to_placed_parts(individual)

            if not placed_parts:
                individual.fitness = 0.0
                individual.utilization = 0.0
                individual.placement_success = False
                return

            # Calculate utilization
            total_part_area = sum(pp.width * pp.height for pp in placed_parts)
            sheet_area = self.sheet_width * self.sheet_height
            utilization = total_part_area / sheet_area if sheet_area > 0 else 0

            # Calculate cut complexity (lower is better)
            cut_complexity = self._calculate_cut_complexity(placed_parts)

            # Multi-objective fitness function
            # Prioritize utilization, but also consider cut complexity
            fitness = (
                utilization * 100  # Primary: material utilization
                + (1.0 / (1.0 + cut_complexity)) * 10  # Secondary: cut simplicity
                + len(placed_parts) * 0.1  # Bonus for placing more parts
            )

            individual.fitness = fitness
            individual.utilization = utilization
            individual.cut_complexity = cut_complexity
            individual.placement_success = True

        except Exception as e:
            logger.debug(f"Individual evaluation failed: {e}")
            individual.fitness = 0.0
            individual.utilization = 0.0
            individual.placement_success = False

    def _individual_to_placed_parts(self, individual: Individual) -> List[PlacedPart]:
        """Convert individual to actual placed parts using simple bin packing."""
        placed_parts = []

        # Simple bottom-left fill algorithm
        occupied_rects = []  # List of (x, y, width, height) rectangles

        for i, part_idx in enumerate(individual.parts_order):
            part = self.parts[part_idx]
            is_rotated = individual.rotations[i]

            # Get part dimensions (possibly rotated)
            if is_rotated and getattr(part, "can_rotate", False):
                part_width = part.height
                part_height = part.width
                rotation_deg = 90
            else:
                part_width = part.width
                part_height = part.height
                rotation_deg = 0

            # Add spacing/kerf
            total_width = part_width + self.spacing_mm
            total_height = part_height + self.spacing_mm

            # Find position using bottom-left fill
            position = self._find_position(total_width, total_height, occupied_rects)

            if position is None:
                # Part doesn't fit, skip it
                continue

            x, y = position

            # Create placed part
            placed_part = PlacedPart(
                id=part.id,
                x=x,
                y=y,
                width=part_width,
                height=part_height,
                rotation_deg=rotation_deg,
                sheet_index=0,
            )
            placed_parts.append(placed_part)

            # Add to occupied rectangles
            occupied_rects.append((x, y, total_width, total_height))

        return placed_parts

    def _find_position(
        self,
        width: float,
        height: float,
        occupied_rects: List[Tuple[float, float, float, float]],
    ) -> Optional[Tuple[float, float]]:
        """Find a position for a rectangle using bottom-left fill."""
        # Try positions starting from bottom-left
        candidates = [(0, 0)]  # Start with origin

        # Add positions based on existing rectangles
        for ox, oy, ow, oh in occupied_rects:
            candidates.extend(
                [
                    (ox + ow, oy),  # Right of existing rect
                    (ox, oy + oh),  # Above existing rect
                    (ox + ow, oy + oh),  # Diagonal from existing rect
                ]
            )

        # Sort candidates by bottom-left preference (y first, then x)
        candidates.sort(key=lambda pos: (pos[1], pos[0]))

        for x, y in candidates:
            # Check if position is within sheet bounds
            if x + width > self.sheet_width or y + height > self.sheet_height:
                continue

            # Check for overlaps with existing rectangles
            new_rect = (x, y, width, height)
            if not self._rectangles_overlap(new_rect, occupied_rects):
                return (x, y)

        return None

    def _rectangles_overlap(
        self,
        rect: Tuple[float, float, float, float],
        rect_list: List[Tuple[float, float, float, float]],
    ) -> bool:
        """Check if rectangle overlaps with any in the list."""
        x1, y1, w1, h1 = rect

        for x2, y2, w2, h2 in rect_list:
            # Check for overlap
            if not (x1 >= x2 + w2 or x2 >= x1 + w1 or y1 >= y2 + h2 or y2 >= y1 + h1):
                return True

        return False

    def _calculate_cut_complexity(self, placed_parts: List[PlacedPart]) -> float:
        """Calculate cut complexity score (lower is better)."""
        if not placed_parts:
            return 0.0

        # Simple complexity metric: number of unique x and y coordinates
        x_coords = set()
        y_coords = set()

        for pp in placed_parts:
            x_coords.add(pp.x)
            x_coords.add(pp.x + pp.width)
            y_coords.add(pp.y)
            y_coords.add(pp.y + pp.height)

        # More unique coordinates = more complex cuts
        return len(x_coords) + len(y_coords)

    def _should_terminate(
        self,
        best_individual: Optional[Individual],
        generation: int,
        start_time: float,
        generations_without_improvement: int,
    ) -> bool:
        """Check if optimization should terminate early."""
        # Time limit
        if (
            self.config.max_time_seconds
            and (time.time() - start_time) > self.config.max_time_seconds
        ):
            return True

        # Target utilization reached
        if (
            best_individual
            and best_individual.utilization >= self.config.target_utilization
        ):
            return True

        # No improvement for many generations
        if generations_without_improvement > 20:
            return True

        return False

    def _create_next_generation(self, population: List[Individual]) -> List[Individual]:
        """Create next generation using selection, crossover, and mutation."""
        # Sort by fitness
        population.sort(key=lambda x: x.fitness, reverse=True)

        next_generation = []

        # Keep elite individuals
        elite_count = min(self.config.elite_size, len(population))
        next_generation.extend(deepcopy(population[:elite_count]))

        # Generate offspring
        while len(next_generation) < self.config.population_size:
            # Tournament selection
            parent1 = self._tournament_selection(population)
            parent2 = self._tournament_selection(population)

            # Crossover
            if random.random() < self.config.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = deepcopy(parent1), deepcopy(parent2)

            # Mutation
            if random.random() < self.config.mutation_rate:
                self._mutate(child1)
            if random.random() < self.config.mutation_rate:
                self._mutate(child2)

            # Reset fitness for evaluation
            child1.fitness = 0.0
            child2.fitness = 0.0

            next_generation.extend([child1, child2])

        return next_generation[: self.config.population_size]

    def _tournament_selection(self, population: List[Individual]) -> Individual:
        """Select individual using tournament selection."""
        tournament = random.sample(
            population, min(self.config.tournament_size, len(population))
        )
        return max(tournament, key=lambda x: x.fitness)

    def _crossover(
        self, parent1: Individual, parent2: Individual
    ) -> Tuple[Individual, Individual]:
        """Create offspring using order crossover for parts order and uniform crossover for rotations."""
        # Order crossover for parts order
        size = len(parent1.parts_order)
        start, end = sorted(random.sample(range(size), 2))

        child1_order = [-1] * size
        child2_order = [-1] * size

        # Copy segments
        child1_order[start:end] = parent1.parts_order[start:end]
        child2_order[start:end] = parent2.parts_order[start:end]

        # Fill remaining positions
        self._fill_remaining_order(child1_order, parent2.parts_order)
        self._fill_remaining_order(child2_order, parent1.parts_order)

        # Uniform crossover for rotations
        child1_rotations = []
        child2_rotations = []

        for i in range(len(parent1.rotations)):
            if random.random() < 0.5:
                child1_rotations.append(parent1.rotations[i])
                child2_rotations.append(parent2.rotations[i])
            else:
                child1_rotations.append(parent2.rotations[i])
                child2_rotations.append(parent1.rotations[i])

        child1 = Individual(parts_order=child1_order, rotations=child1_rotations)
        child2 = Individual(parts_order=child2_order, rotations=child2_rotations)

        return child1, child2

    def _fill_remaining_order(
        self, child_order: List[int], parent_order: List[int]
    ) -> None:
        """Fill remaining positions in child order from parent."""
        used = set(x for x in child_order if x != -1)
        parent_idx = 0

        for i in range(len(child_order)):
            if child_order[i] == -1:
                while parent_order[parent_idx] in used:
                    parent_idx += 1
                child_order[i] = parent_order[parent_idx]
                used.add(parent_order[parent_idx])
                parent_idx += 1

    def _mutate(self, individual: Individual) -> None:
        """Apply mutation to individual."""
        # Mutation for parts order: swap two random positions
        if len(individual.parts_order) > 1:
            i, j = random.sample(range(len(individual.parts_order)), 2)
            individual.parts_order[i], individual.parts_order[j] = (
                individual.parts_order[j],
                individual.parts_order[i],
            )

        # Mutation for rotations: flip random rotation (if part can rotate)
        if individual.rotations:
            idx = random.randint(0, len(individual.rotations) - 1)
            part = self.parts[idx]
            if getattr(part, "can_rotate", False):
                individual.rotations[idx] = not individual.rotations[idx]


@performance_monitor("Genetic Algorithm Nesting", threshold_seconds=5.0)
def genetic_nest_parts(
    parts: List[Part],
    sheet_width: float,
    sheet_height: float,
    kerf_mm: float = 0,
    spacing_mm: float = 0,
    config: Optional[GeneticConfig] = None,
) -> List[PlacedPart]:
    """High-level function to run genetic algorithm nesting."""
    optimizer = GeneticNestingOptimizer(config)
    return optimizer.optimize(parts, sheet_width, sheet_height, kerf_mm, spacing_mm)
