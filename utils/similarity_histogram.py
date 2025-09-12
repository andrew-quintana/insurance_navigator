"""
Similarity Histogram Utility for RAG Tool

This module provides adaptive histogram generation for cosine similarity scores
to help understand the distribution of similarity scores from RAG tool execution.
"""

import sys
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import standard library logging to avoid conflicts with utils.logging
import logging as std_logging


@dataclass
class HistogramBucket:
    """Represents a histogram bucket with range and count"""
    min_similarity: float
    max_similarity: float
    count: int
    percentage: float
    
    def __str__(self):
        return f"[{self.min_similarity:.3f}-{self.max_similarity:.3f}]: {self.count} ({self.percentage:.1f}%)"


class SimilarityHistogram:
    """
    Adaptive histogram generator for cosine similarity scores.
    
    Features:
    - Adaptive bucket sizing based on data distribution
    - Handles edge cases (all zeros, single values, etc.)
    - Provides detailed statistics
    - Generates human-readable output
    """
    
    def __init__(self, min_buckets: int = 5, max_buckets: int = 20):
        self.min_buckets = min_buckets
        self.max_buckets = max_buckets
        self.logger = std_logging.getLogger(__name__)
    
    def generate_histogram(self, similarities: List[float], threshold: float = 0.4) -> Dict[str, Any]:
        """
        Generate adaptive histogram for similarity scores.
        
        Args:
            similarities: List of similarity scores
            threshold: Similarity threshold for filtering
            
        Returns:
            Dict containing histogram data and statistics
        """
        if not similarities:
            return self._empty_histogram()
        
        # Filter out None values and convert to float
        valid_similarities = [float(s) for s in similarities if s is not None]
        
        if not valid_similarities:
            return self._empty_histogram()
        
        # Calculate statistics
        stats = self._calculate_statistics(valid_similarities, threshold)
        
        # Generate adaptive buckets
        buckets = self._generate_adaptive_buckets(valid_similarities)
        
        # Count similarities in each bucket
        bucket_counts = self._count_in_buckets(valid_similarities, buckets)
        
        # Create histogram buckets
        histogram_buckets = []
        for i, bucket in enumerate(buckets):
            count = bucket_counts[i]
            percentage = (count / len(valid_similarities)) * 100 if valid_similarities else 0
            
            histogram_buckets.append(HistogramBucket(
                min_similarity=bucket[0],
                max_similarity=bucket[1],
                count=count,
                percentage=percentage
            ))
        
        return {
            "total_similarities": len(valid_similarities),
            "threshold": threshold,
            "statistics": stats,
            "buckets": histogram_buckets,
            "above_threshold": stats["above_threshold"],
            "below_threshold": stats["below_threshold"],
            "threshold_percentage": stats["threshold_percentage"]
        }
    
    def _empty_histogram(self) -> Dict[str, Any]:
        """Return empty histogram for no data"""
        return {
            "total_similarities": 0,
            "threshold": 0.4,
            "statistics": {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "above_threshold": 0,
                "below_threshold": 0,
                "threshold_percentage": 0.0
            },
            "buckets": [],
            "above_threshold": 0,
            "below_threshold": 0,
            "threshold_percentage": 0.0
        }
    
    def _calculate_statistics(self, similarities: List[float], threshold: float) -> Dict[str, float]:
        """Calculate basic statistics for similarity scores"""
        similarities.sort()
        
        min_val = similarities[0]
        max_val = similarities[-1]
        mean_val = sum(similarities) / len(similarities)
        
        # Calculate median
        n = len(similarities)
        if n % 2 == 0:
            median_val = (similarities[n//2 - 1] + similarities[n//2]) / 2
        else:
            median_val = similarities[n//2]
        
        # Calculate standard deviation
        variance = sum((x - mean_val) ** 2 for x in similarities) / len(similarities)
        std_val = math.sqrt(variance)
        
        # Count above/below threshold
        above_threshold = sum(1 for x in similarities if x >= threshold)
        below_threshold = len(similarities) - above_threshold
        threshold_percentage = (above_threshold / len(similarities)) * 100
        
        return {
            "min": min_val,
            "max": max_val,
            "mean": mean_val,
            "median": median_val,
            "std": std_val,
            "above_threshold": above_threshold,
            "below_threshold": below_threshold,
            "threshold_percentage": threshold_percentage
        }
    
    def _generate_adaptive_buckets(self, similarities: List[float]) -> List[tuple]:
        """Generate adaptive buckets based on data distribution"""
        min_val = similarities[0]
        max_val = similarities[-1]
        
        # Handle edge case where all values are the same
        if min_val == max_val:
            return [(min_val, max_val)]
        
        # Calculate optimal number of buckets
        n = len(similarities)
        optimal_buckets = min(max(self.min_buckets, int(math.sqrt(n))), self.max_buckets)
        
        # Create buckets with adaptive sizing
        bucket_width = (max_val - min_val) / optimal_buckets
        
        buckets = []
        for i in range(optimal_buckets):
            start = min_val + i * bucket_width
            end = min_val + (i + 1) * bucket_width
            
            # Make the last bucket inclusive of max_val
            if i == optimal_buckets - 1:
                end = max_val
            
            buckets.append((start, end))
        
        return buckets
    
    def _count_in_buckets(self, similarities: List[float], buckets: List[tuple]) -> List[int]:
        """Count similarities in each bucket"""
        counts = [0] * len(buckets)
        
        for similarity in similarities:
            for i, (min_val, max_val) in enumerate(buckets):
                if min_val <= similarity < max_val or (i == len(buckets) - 1 and similarity == max_val):
                    counts[i] += 1
                    break
        
        return counts
    
    def format_histogram(self, histogram_data: Dict[str, Any]) -> str:
        """Format histogram data as a human-readable string"""
        if histogram_data["total_similarities"] == 0:
            return "No similarity data available"
        
        lines = []
        lines.append("Similarity Score Distribution:")
        lines.append("=" * 50)
        
        # Statistics
        stats = histogram_data["statistics"]
        lines.append(f"Total similarities: {histogram_data['total_similarities']}")
        lines.append(f"Threshold: {histogram_data['threshold']}")
        lines.append(f"Range: [{stats['min']:.3f} - {stats['max']:.3f}]")
        lines.append(f"Mean: {stats['mean']:.3f}")
        lines.append(f"Median: {stats['median']:.3f}")
        lines.append(f"Std Dev: {stats['std']:.3f}")
        lines.append(f"Above threshold: {stats['above_threshold']} ({stats['threshold_percentage']:.1f}%)")
        lines.append("")
        
        # Histogram buckets
        lines.append("Histogram:")
        lines.append("-" * 30)
        
        for bucket in histogram_data["buckets"]:
            # Create visual bar
            bar_length = int(bucket.percentage / 2)  # Scale for display
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            lines.append(f"{str(bucket):<30} {bar}")
        
        return "\n".join(lines)
    
    def log_histogram(self, similarities: List[float], threshold: float = 0.4, logger: Optional[Any] = None):
        """Generate and log histogram for similarity scores"""
        if logger is None:
            logger = self.logger
        
        histogram_data = self.generate_histogram(similarities, threshold)
        formatted_histogram = self.format_histogram(histogram_data)
        
        logger.info(f"RAG Similarity Histogram:\n{formatted_histogram}")
        
        return histogram_data


# Convenience function for quick histogram generation
def log_similarity_histogram(similarities: List[float], threshold: float = 0.4, logger: Optional[Any] = None):
    """
    Quick function to generate and log similarity histogram.
    
    Args:
        similarities: List of similarity scores
        threshold: Similarity threshold for filtering
        logger: Logger instance (optional)
    """
    histogram = SimilarityHistogram()
    return histogram.log_histogram(similarities, threshold, logger)


def get_similarity_statistics(similarities: List[float], threshold: float = 0.4) -> Dict[str, Any]:
    """
    Get similarity statistics without logging.
    
    Args:
        similarities: List of similarity scores
        threshold: Similarity threshold for filtering
        
    Returns:
        Dict containing similarity statistics
    """
    histogram = SimilarityHistogram()
    return histogram.generate_histogram(similarities, threshold)


if __name__ == "__main__":
    # Test the histogram utility
    import random
    
    # Generate test data
    test_similarities = [random.uniform(0.0, 1.0) for _ in range(100)]
    
    # Add some specific values for testing
    test_similarities.extend([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    
    # Test histogram generation
    histogram = SimilarityHistogram()
    histogram_data = histogram.generate_histogram(test_similarities, threshold=0.4)
    
    print("Test Histogram:")
    print(histogram.format_histogram(histogram_data))
