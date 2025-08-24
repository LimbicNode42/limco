#!/usr/bin/env python3
"""
Clone Size Analyzer - Analyze why clone is larger than expected
"""
import os
import struct
from typing import Dict, Any

class CloneSizeAnalyzer:
    def __init__(self):
        self.sector_size = 512
    
    def analyze_oversized_clone(self, clone_path: str, expected_size_gb: int = 128) -> Dict[str, Any]:
        """Analyze why clone is larger than expected."""
        print(f"🔍 ANALYZING OVERSIZED CLONE")
        print(f"Clone: {os.path.basename(clone_path)}")
        print(f"Expected: ~{expected_size_gb} GB")
        
        if not os.path.exists(clone_path):
            return {'error': 'Clone file not found'}
        
        actual_size = os.path.getsize(clone_path)
        actual_gb = actual_size / (1024**3)
        print(f"Actual:   {actual_gb:.2f} GB ({actual_size:,} bytes)")
        
        analysis = {
            'clone_path': clone_path,
            'expected_gb': expected_size_gb,
            'actual_gb': actual_gb,
            'actual_bytes': actual_size,
            'oversized_by_gb': actual_gb - expected_size_gb,
            'issues_found': []
        }
        
        # Check for partition table issues
        print(f"\n[STEP 1] Analyzing partition structure...")
        partition_info = self.analyze_partitions(clone_path)
        analysis['partition_info'] = partition_info
        
        if partition_info['issues']:
            analysis['issues_found'].extend(partition_info['issues'])
        
        # Check for data patterns beyond expected size
        print(f"\n[STEP 2] Checking data patterns...")
        pattern_info = self.check_data_patterns(clone_path, expected_size_gb * (1024**3))
        analysis['pattern_info'] = pattern_info
        
        if pattern_info['issues']:
            analysis['issues_found'].extend(pattern_info['issues'])
        
        # Provide recommendations
        print(f"\n[STEP 3] Generating recommendations...")
        recommendations = self.generate_recommendations(analysis)
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def analyze_partitions(self, clone_path: str) -> Dict[str, Any]:
        """Analyze partition table and calculate expected size."""
        try:
            with open(clone_path, 'rb') as f:
                # Read MBR
                mbr = f.read(512)
                
                partition_info = {
                    'partitions_found': [],
                    'expected_size_from_partitions': 0,
                    'issues': []
                }
                
                # Parse partition table (starts at offset 446)
                for i in range(4):
                    offset = 446 + (i * 16)
                    part_type = mbr[offset + 4]
                    
                    if part_type != 0:  # Non-empty partition
                        start_lba = struct.unpack('<L', mbr[offset + 8:offset + 12])[0]
                        size_sectors = struct.unpack('<L', mbr[offset + 12:offset + 16])[0]
                        end_lba = start_lba + size_sectors
                        
                        partition = {
                            'number': i + 1,
                            'type': f'0x{part_type:02X}',
                            'start_lba': start_lba,
                            'size_sectors': size_sectors,
                            'size_mb': (size_sectors * 512) / (1024**2),
                            'end_lba': end_lba
                        }
                        
                        partition_info['partitions_found'].append(partition)
                        print(f"   Partition {i+1}: Type=0x{part_type:02X}, Start={start_lba}, Size={partition['size_mb']:.1f}MB")
                
                # Calculate expected size based on partitions
                if partition_info['partitions_found']:
                    max_end_lba = max(p['end_lba'] for p in partition_info['partitions_found'])
                    expected_size = max_end_lba * 512
                    partition_info['expected_size_from_partitions'] = expected_size
                    
                    expected_gb = expected_size / (1024**3)
                    print(f"   Expected size from partitions: {expected_gb:.2f} GB")
                    
                    # Check if clone is much larger than partition table indicates
                    actual_size = os.path.getsize(clone_path)
                    if actual_size > expected_size * 2:  # More than 2x expected
                        partition_info['issues'].append(
                            f"Clone is {actual_size / expected_size:.1f}x larger than partition table indicates"
                        )
                
                return partition_info
                
        except Exception as e:
            return {'error': f'Failed to analyze partitions: {e}', 'issues': []}
    
    def check_data_patterns(self, clone_path: str, expected_size: int) -> Dict[str, Any]:
        """Check data patterns beyond the expected size."""
        pattern_info = {
            'has_data_beyond_expected': False,
            'zero_regions': [],
            'pattern_regions': [],
            'issues': []
        }
        
        try:
            file_size = os.path.getsize(clone_path)
            
            if file_size > expected_size:
                # Check several points beyond expected size
                sample_points = [
                    expected_size,
                    expected_size + (100 * 1024 * 1024),  # +100MB
                    expected_size + (1024 * 1024 * 1024),  # +1GB
                    min(file_size - 4096, expected_size + (2 * 1024 * 1024 * 1024))  # +2GB or near end
                ]
                
                with open(clone_path, 'rb') as f:
                    for point in sample_points:
                        if point >= file_size:
                            continue
                        
                        f.seek(point)
                        sample = f.read(4096)  # Read 4KB sample
                        
                        # Check if it's all zeros
                        if sample == b'\x00' * len(sample):
                            pattern_info['zero_regions'].append({
                                'offset': point,
                                'offset_gb': point / (1024**3),
                                'pattern': 'all_zeros'
                            })
                        elif len(set(sample)) < 10:  # Very few unique bytes (likely pattern)
                            pattern_info['pattern_regions'].append({
                                'offset': point,
                                'offset_gb': point / (1024**3),
                                'pattern': f'repetitive (unique bytes: {len(set(sample))})'
                            })
                        else:
                            pattern_info['has_data_beyond_expected'] = True
                            print(f"   Found actual data at {point / (1024**3):.2f} GB offset")
                
                # Analyze findings
                zero_count = len(pattern_info['zero_regions'])
                pattern_count = len(pattern_info['pattern_regions'])
                
                if zero_count > 0:
                    print(f"   Found {zero_count} zero-filled regions beyond expected size")
                
                if pattern_count > 0:
                    print(f"   Found {pattern_count} repetitive pattern regions")
                
                if not pattern_info['has_data_beyond_expected'] and (zero_count > 0 or pattern_count > 0):
                    pattern_info['issues'].append(
                        "Clone contains mostly empty/repetitive data beyond expected drive size"
                    )
        
        except Exception as e:
            pattern_info['error'] = f'Pattern analysis failed: {e}'
        
        return pattern_info
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> list:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        actual_gb = analysis['actual_gb']
        expected_gb = analysis['expected_gb']
        oversized_by = analysis['oversized_by_gb']
        
        if oversized_by > 50:  # More than 50GB oversized
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Create a trimmed clone',
                'reason': f'Clone is {oversized_by:.1f}GB larger than expected',
                'command': f'python trim_clone.py "{analysis["clone_path"]}" {expected_gb}'
            })
        
        partition_info = analysis.get('partition_info', {})
        if partition_info.get('expected_size_from_partitions'):
            expected_from_partitions_gb = partition_info['expected_size_from_partitions'] / (1024**3)
            
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Use partition-based size',
                'reason': f'Partition table indicates size should be {expected_from_partitions_gb:.2f}GB',
                'command': f'python trim_clone.py "{analysis["clone_path"]}" {expected_from_partitions_gb:.0f}'
            })
        
        pattern_info = analysis.get('pattern_info', {})
        if pattern_info.get('issues'):
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Remove empty/repetitive data',
                'reason': 'Clone contains excessive empty or repetitive data',
                'command': 'Trim clone to actual data size'
            })
        
        # Always recommend testing current clone
        recommendations.append({
            'priority': 'LOW',
            'action': 'Test current oversized clone',
            'reason': 'Current clone might still work despite oversizing',
            'command': f'python test_mount.py "{analysis["clone_path"]}"'
        })
        
        return recommendations
    
    def print_analysis_report(self, analysis: Dict[str, Any]):
        """Print a formatted analysis report."""
        print(f"\n{'='*60}")
        print(f"📊 CLONE SIZE ANALYSIS REPORT")
        print(f"{'='*60}")
        
        print(f"File: {os.path.basename(analysis['clone_path'])}")
        print(f"Expected Size: {analysis['expected_gb']} GB")
        print(f"Actual Size:   {analysis['actual_gb']:.2f} GB")
        print(f"Oversized By:  {analysis['oversized_by_gb']:.2f} GB ({analysis['oversized_by_gb']/analysis['expected_gb']*100:.1f}% larger)")
        
        if analysis['issues_found']:
            print(f"\n🔴 ISSUES FOUND:")
            for i, issue in enumerate(analysis['issues_found'], 1):
                print(f"   {i}. {issue}")
        
        partition_info = analysis.get('partition_info', {})
        if partition_info.get('partitions_found'):
            print(f"\n📋 PARTITION INFORMATION:")
            for p in partition_info['partitions_found']:
                print(f"   Partition {p['number']}: {p['type']} - {p['size_mb']:.0f}MB")
        
        if analysis['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(analysis['recommendations'], 1):
                print(f"   {i}. [{rec['priority']}] {rec['action']}")
                print(f"      Reason: {rec['reason']}")
                if rec.get('command'):
                    print(f"      Command: {rec['command']}")
                print()

def main():
    import sys
    if len(sys.argv) not in [2, 3]:
        print("Usage: python analyze_clone_size.py <clone_path> [expected_size_gb]")
        sys.exit(1)
    
    clone_path = sys.argv[1]
    expected_size_gb = int(sys.argv[2]) if len(sys.argv) > 2 else 128
    
    analyzer = CloneSizeAnalyzer()
    analysis = analyzer.analyze_oversized_clone(clone_path, expected_size_gb)
    
    if 'error' in analysis:
        print(f"❌ Error: {analysis['error']}")
        sys.exit(1)
    
    analyzer.print_analysis_report(analysis)

if __name__ == "__main__":
    main()
