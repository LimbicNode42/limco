"""
LLM-powered analysis and planning for drive recovery operations.
Uses Claude 3.5 Sonnet for intelligent analysis of drive corruption patterns and recovery strategies.
"""

import os
from typing import Dict, List, Optional, Tuple
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate


class RecoveryAnalystLLM:
    """
    LLM-powered analyst for drive recovery operations using Claude 3.5 Sonnet.
    """
    
    def __init__(self):
        """Initialize the Claude 3.5 Sonnet model."""
        self.model = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1  # Low temperature for consistent, technical analysis
        )
    
    def analyze_drive_corruption(self, analysis_results: Dict[str, str], 
                               drive_info: Optional[Dict] = None) -> Tuple[str, str, List[str]]:
        """
        Analyze drive corruption patterns using LLM to provide intelligent insights.
        
        Args:
            analysis_results: Dictionary of partition -> status mappings
            drive_info: Optional drive information (model, size, etc.)
        
        Returns:
            Tuple of (analysis_summary, severity_assessment, specific_recommendations)
        """
        
        # Prepare drive context
        drive_context = ""
        if drive_info:
            drive_context = f"""
Drive Information:
- Model: {drive_info.get('name', 'Unknown')}
- Size: {drive_info.get('size', 'Unknown')}
- Type: {drive_info.get('type', 'Unknown')}
"""
        
        # Format analysis results
        corruption_details = "\n".join([
            f"- {partition}: {status}" for partition, status in analysis_results.items()
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert data recovery specialist with deep knowledge of filesystem corruption, boot sector issues, and partition table problems. 

Your role is to analyze drive corruption patterns and provide:
1. Clear technical analysis in plain English
2. Severity assessment (Critical/High/Medium/Low)
3. Specific, actionable recovery recommendations
4. Risk assessment for different recovery approaches

Focus on practical, safe recovery methods that preserve as much data as possible. Always prioritize data safety over speed of recovery."""),
            
            HumanMessage(content=f"""Please analyze this drive corruption scenario:

{drive_context}

Partition Analysis Results:
{corruption_details}

Provide your analysis in this exact format:

ANALYSIS SUMMARY:
[2-3 sentences explaining what's wrong with the drive]

SEVERITY: [Critical/High/Medium/Low]

SPECIFIC RECOMMENDATIONS:
1. [First recommended action]
2. [Second recommended action]  
3. [Third recommended action if needed]

RISK ASSESSMENT:
[Brief explanation of success probability and potential data loss risks]""")
        ])
        
        try:
            response = self.model.invoke(prompt.format_messages())
            content = response.content
            
            # Parse the structured response
            analysis_summary = self._extract_section(content, "ANALYSIS SUMMARY:")
            severity = self._extract_section(content, "SEVERITY:")
            recommendations_text = self._extract_section(content, "SPECIFIC RECOMMENDATIONS:")
            risk_assessment = self._extract_section(content, "RISK ASSESSMENT:")
            
            # Parse recommendations into list
            recommendations = []
            if recommendations_text:
                lines = recommendations_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith(('1.', '2.', '3.', '•', '-'))):
                        # Clean up the recommendation text
                        clean_rec = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                        recommendations.append(clean_rec)
            
            # Combine analysis with risk assessment
            full_analysis = f"{analysis_summary}\n\nRisk Assessment: {risk_assessment}"
            
            return full_analysis, severity.strip(), recommendations
            
        except Exception as e:
            # Fallback analysis if LLM fails
            return self._fallback_analysis(analysis_results), "Medium", ["Run standard filesystem repair tools", "Consider professional recovery services"]
    
    def generate_recovery_plan(self, analysis_results: Dict[str, str], 
                             severity: str, recommendations: List[str]) -> str:
        """
        Generate a detailed, step-by-step recovery plan using LLM.
        
        Args:
            analysis_results: Partition analysis results
            severity: Severity level from previous analysis
            recommendations: Specific recommendations from analysis
        
        Returns:
            Detailed recovery plan as formatted string
        """
        
        corruption_summary = "\n".join([
            f"- {partition}: {status}" for partition, status in analysis_results.items()
        ])
        
        recommendations_text = "\n".join([f"• {rec}" for rec in recommendations])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are creating a detailed recovery plan for drive corruption. Your plan must be:

1. Step-by-step with clear instructions
2. Safe-first approach (always work on clones)
3. Include specific commands/tools where appropriate
4. Explain WHY each step is necessary
5. Include verification steps
6. Provide fallback options if steps fail

Format your response as a numbered, actionable plan that a technical user can follow."""),
            
            HumanMessage(content=f"""Create a detailed recovery plan for this corruption scenario:

Corruption Status:
{corruption_summary}

Severity Level: {severity}

Key Recommendations:
{recommendations_text}

Please provide a step-by-step recovery plan that includes:
- Specific tools to use (testdisk, photorec, fsck, etc.)
- Safety verification steps
- Expected outcomes for each step
- Alternative approaches if primary method fails
- Final data verification procedures

Remember: All operations should be performed on the cloned drive to protect original data.""")
        ])
        
        try:
            response = self.model.invoke(prompt.format_messages())
            return response.content
            
        except Exception as e:
            # Fallback plan if LLM fails
            return self._fallback_recovery_plan(analysis_results, severity)
    
    def interpret_technical_output(self, tool_output: str, tool_name: str) -> str:
        """
        Interpret technical tool output and explain in plain English.
        
        Args:
            tool_output: Raw output from recovery tools
            tool_name: Name of the tool that generated the output
            
        Returns:
            Plain English explanation of what the output means
        """
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are interpreting output from the {tool_name} tool used in data recovery. 

Your job is to:
1. Explain what the technical output means in plain English
2. Identify any critical issues or warnings
3. Suggest next steps based on the output
4. Highlight any successful operations or concerning errors

Be concise but thorough - focus on actionable insights."""),
            
            HumanMessage(content=f"""Please interpret this {tool_name} output:

{tool_output}

Explain what this means for the data recovery process and what actions should be taken next.""")
        ])
        
        try:
            response = self.model.invoke(prompt.format_messages())
            return response.content
            
        except Exception as e:
            return f"Unable to interpret {tool_name} output due to LLM error: {str(e)}"
    
    def _extract_section(self, content: str, section_header: str) -> str:
        """Extract a specific section from structured LLM response."""
        lines = content.split('\n')
        in_section = False
        section_lines = []
        
        for line in lines:
            if line.strip().startswith(section_header):
                in_section = True
                # Include the content after the header on the same line
                header_content = line.replace(section_header, '').strip()
                if header_content:
                    section_lines.append(header_content)
                continue
            elif in_section and line.strip().startswith(('ANALYSIS', 'SEVERITY', 'SPECIFIC', 'RISK')):
                # Hit another section header, stop
                break
            elif in_section:
                section_lines.append(line)
        
        return '\n'.join(section_lines).strip()
    
    def _fallback_analysis(self, analysis_results: Dict[str, str]) -> str:
        """Provide basic analysis if LLM fails."""
        corrupted_count = sum(1 for status in analysis_results.values() if status == "corrupted")
        repair_count = sum(1 for status in analysis_results.values() if status == "needs_repair")
        
        if corrupted_count > 0:
            return f"Drive shows {corrupted_count} corrupted partition(s) and {repair_count} partition(s) needing repair. Boot sector or partition table corruption likely."
        elif repair_count > 0:
            return f"Drive has {repair_count} partition(s) with minor filesystem errors that can likely be repaired."
        else:
            return "Drive analysis shows no major corruption detected."
    
    def _fallback_recovery_plan(self, analysis_results: Dict[str, str], severity: str) -> str:
        """Provide basic recovery plan if LLM fails."""
        plan = f"""Recovery Plan (Severity: {severity})

1. Verify clone integrity
   - Ensure cloned drive matches original size
   - Verify clone was created without errors

2. Run filesystem checks
   - Use fsck (Linux) or chkdsk (Windows) on affected partitions
   - Document any errors found

3. Attempt automated repair
   - Run repair tools in read-only mode first
   - If safe, proceed with write operations

4. Boot sector recovery (if needed)
   - Use testdisk for partition table reconstruction
   - Use photorec for file recovery if filesystem repair fails

5. Verification
   - Mount recovered partitions to verify access
   - Check critical files and boot functionality
   - Create backup of recovered data

Note: This is a basic plan. Consider professional recovery services for critical data."""
        
        return plan
