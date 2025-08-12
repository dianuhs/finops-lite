"""
Caching system for FinOps Lite.
Provides intelligent caching of API responses to improve performance and reduce costs.
"""

import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, Union
from dataclasses import dataclass, asdict
from rich.console import Console

console = Console()

@dataclass
class CacheEntry:
    """Represents a cached entry with metadata."""
    data: Any
    timestamp: float
    ttl_seconds: int
    key: str
    api_call_cost: float = 0.01  # Default Cost Explorer API cost
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl_seconds
    
    @property
    def age_minutes(self) -> float:
        """Get age of cache entry in minutes."""
        return (time.time() - self.timestamp) / 60
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'data': self.data,
            'timestamp': self.timestamp,
            'ttl_seconds': self.ttl_seconds,
            'key': self.key,
            'api_call_cost': self.api_call_cost
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(**data)

class CacheManager:
    """Manages caching for API responses and expensive operations."""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_cache_size_mb: int = 50):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files (default: ~/.finops/cache)
            max_cache_size_mb: Maximum cache size in MB
        """
        self.cache_dir = cache_dir or Path.home() / '.finops' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size_mb = max_cache_size_mb
        self.cache_file = self.cache_dir / 'api_cache.json'
        
        # Default TTL values for different types of data
        self.default_ttls = {
            'cost_data': 3600,      # 1 hour for cost data
            'account_info': 86400,   # 24 hours for account info
            'service_list': 86400,   # 24 hours for service listings
            'rightsizing': 3600,     # 1 hour for rightsizing recommendations
            'tags': 1800,           # 30 minutes for tag data
            'config': 300,          # 5 minutes for configuration
        }
        
        # Load existing cache
        self._cache: Dict[str, CacheEntry] = self._load_cache()
        
        # Performance metrics
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls_saved': 0,
            'cost_savings': 0.0,
            'total_cache_operations': 0
        }
    
    def _generate_key(self, operation: str, **kwargs) -> str:
        """Generate a unique cache key based on operation and parameters."""
        # Sort kwargs for consistent key generation
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, sort_keys=True, default=str)
        
        # Create hash of operation + parameters
        content = f"{operation}:{params_str}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _load_cache(self) -> Dict[str, CacheEntry]:
        """Load cache from disk."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                cache = {}
                for key, entry_data in cache_data.items():
                    try:
                        cache[key] = CacheEntry.from_dict(entry_data)
                    except Exception:
                        # Skip corrupted entries
                        continue
                
                # Clean expired entries
                self._clean_expired_entries(cache)
                return cache
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load cache: {e}[/yellow]")
        
        return {}
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            # Clean expired entries before saving
            self._clean_expired_entries(self._cache)
            
            # Convert to serializable format
            cache_data = {
                key: entry.to_dict() 
                for key, entry in self._cache.items()
            }
            
            # Check cache size and clean if necessary
            self._manage_cache_size(cache_data)
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save cache: {e}[/yellow]")
    
    def _clean_expired_entries(self, cache: Dict[str, CacheEntry]):
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in cache.items() 
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del cache[key]
        
        if expired_keys:
            console.print(f"[dim]Cleaned {len(expired_keys)} expired cache entries[/dim]")
    
    def _manage_cache_size(self, cache_data: Dict):
        """Manage cache size by removing oldest entries if needed."""
        cache_size_mb = len(json.dumps(cache_data).encode()) / (1024 * 1024)
        
        if cache_size_mb > self.max_cache_size_mb:
            # Sort by timestamp and remove oldest entries
            sorted_entries = sorted(
                cache_data.items(),
                key=lambda x: x[1]['timestamp']
            )
            
            # Remove oldest 25% of entries
            remove_count = len(sorted_entries) // 4
            for key, _ in sorted_entries[:remove_count]:
                del cache_data[key]
            
            console.print(f"[dim]Cache size limit reached. Removed {remove_count} oldest entries[/dim]")
    
    def get(self, operation: str, data_type: str = 'cost_data', **kwargs) -> Optional[Any]:
        """
        Get cached data.
        
        Args:
            operation: Operation name (e.g., 'get_cost_overview')
            data_type: Type of data for TTL selection
            **kwargs: Parameters used to generate cache key
        
        Returns:
            Cached data if available and not expired, None otherwise
        """
        key = self._generate_key(operation, **kwargs)
        self.metrics['total_cache_operations'] += 1
        
        if key in self._cache:
            entry = self._cache[key]
            
            if not entry.is_expired:
                self.metrics['cache_hits'] += 1
                self.metrics['api_calls_saved'] += 1
                self.metrics['cost_savings'] += entry.api_call_cost
                
                console.print(f"[green]💾 Cache hit[/green] [dim]({entry.age_minutes:.1f}m old)[/dim]")
                return entry.data
            else:
                # Remove expired entry
                del self._cache[key]
                console.print(f"[yellow]🕐 Cache expired[/yellow] [dim]({entry.age_minutes:.1f}m old)[/dim]")
        
        self.metrics['cache_misses'] += 1
        return None
    
    def set(self, operation: str, data: Any, data_type: str = 'cost_data', **kwargs):
        """
        Cache data.
        
        Args:
            operation: Operation name
            data: Data to cache
            data_type: Type of data for TTL selection
            **kwargs: Parameters used to generate cache key
        """
        key = self._generate_key(operation, **kwargs)
        ttl = self.default_ttls.get(data_type, 3600)
        
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl_seconds=ttl,
            key=key,
            api_call_cost=0.01 if 'cost' in operation.lower() else 0.0
        )
        
        self._cache[key] = entry
        console.print(f"[blue]💾 Cached result[/blue] [dim](TTL: {ttl//60}m)[/dim]")
        
        # Save to disk periodically
        if len(self._cache) % 10 == 0:  # Save every 10 operations
            self._save_cache()
    
    def invalidate(self, operation: str = None, **kwargs):
        """
        Invalidate cache entries.
        
        Args:
            operation: Specific operation to invalidate (None for all)
            **kwargs: Parameters to match for invalidation
        """
        if operation:
            key = self._generate_key(operation, **kwargs)
            if key in self._cache:
                del self._cache[key]
                console.print(f"[yellow]🗑️  Invalidated cache for {operation}[/yellow]")
        else:
            # Invalidate all
            count = len(self._cache)
            self._cache.clear()
            console.print(f"[yellow]🗑️  Cleared all cache ({count} entries)[/yellow]")
        
        self._save_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_ops = self.metrics['cache_hits'] + self.metrics['cache_misses']
        hit_rate = (self.metrics['cache_hits'] / total_ops * 100) if total_ops > 0 else 0
        
        cache_size_mb = 0
        if self.cache_file.exists():
            cache_size_mb = self.cache_file.stat().st_size / (1024 * 1024)
        
        return {
            'cache_entries': len(self._cache),
            'cache_size_mb': round(cache_size_mb, 2),
            'hit_rate_percent': round(hit_rate, 1),
            'api_calls_saved': self.metrics['api_calls_saved'],
            'estimated_cost_savings': round(self.metrics['cost_savings'], 2),
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
        }
    
    def cleanup(self):
        """Clean up cache and save to disk."""
        self._clean_expired_entries(self._cache)
        self._save_cache()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - save cache."""
        self.cleanup()