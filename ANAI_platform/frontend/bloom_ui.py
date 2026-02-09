"""
Bloom's Taxonomy UI Components for Streamlit.

Provides interactive controls for selecting and configuring Bloom's taxonomy
levels for paper generation with dynamic options.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go


# ============================================================================
# BLOOM LEVEL DEFINITIONS
# ============================================================================

BLOOM_LEVELS = {
    "Remember": {
        "description": "Recall facts and basic concepts",
        "icon": "🧠",
        "color": "#3498db",
        "examples": ["Define", "Recall", "Identify", "List"]
    },
    "Understand": {
        "description": "Explain ideas or concepts",
        "icon": "💡",
        "color": "#2ecc71",
        "examples": ["Explain", "Summarize", "Classify", "Discuss"]
    },
    "Apply": {
        "description": "Use information in new situations",
        "icon": "🎯",
        "color": "#f39c12",
        "examples": ["Solve", "Implement", "Demonstrate", "Execute"]
    },
    "Analyze": {
        "description": "Draw connections among ideas",
        "icon": "🔍",
        "color": "#e74c3c",
        "examples": ["Compare", "Contrast", "Distinguish", "Examine"]
    },
    "Evaluate": {
        "description": "Justify a stand or decision",
        "icon": "⚖️",
        "color": "#9b59b6",
        "examples": ["Judge", "Critique", "Appraise", "Justify"]
    },
    "Create": {
        "description": "Produce new or original work",
        "icon": "🚀",
        "color": "#e91e63",
        "examples": ["Design", "Produce", "Invent", "Compose"]
    }
}

QUESTION_TYPE_BLOOM_MAPPING = {
    "Multiple Choice": ["Remember", "Understand", "Apply"],
    "True/False": ["Remember", "Understand"],
    "Fill in the Blank": ["Remember", "Understand"],
    "Short Answer": ["Understand", "Apply", "Analyze"],
    "Long Answer": ["Apply", "Analyze", "Evaluate", "Create"],
    "Numerical Problem": ["Apply", "Analyze"],
    "Code Implementation": ["Apply", "Analyze", "Create"],
    "Code Output Prediction": ["Understand", "Apply", "Analyze"],
    "Scenario-Based": ["Apply", "Analyze", "Evaluate"],
    "Diagram-Based": ["Understand", "Apply", "Analyze"],
}

PRESET_DISTRIBUTIONS = {
    "Balanced (Default)": {
        "Remember": 10,
        "Understand": 25,
        "Apply": 30,
        "Analyze": 20,
        "Evaluate": 10,
        "Create": 5,
        "description": "Good for general assessment, mixed cognitive levels"
    },
    "Conceptual Focus": {
        "Remember": 15,
        "Understand": 40,
        "Apply": 25,
        "Analyze": 15,
        "Evaluate": 5,
        "Create": 0,
        "description": "For introductory/foundation courses"
    },
    "Application-Focused": {
        "Remember": 5,
        "Understand": 15,
        "Apply": 40,
        "Analyze": 30,
        "Evaluate": 10,
        "Create": 0,
        "description": "For practical/hands-on courses"
    },
    "Higher-Order Thinking": {
        "Remember": 0,
        "Understand": 10,
        "Apply": 20,
        "Analyze": 30,
        "Evaluate": 25,
        "Create": 15,
        "description": "For advanced/MTech level assessments"
    },
    "Research/Design Focus": {
        "Remember": 0,
        "Understand": 5,
        "Apply": 15,
        "Analyze": 25,
        "Evaluate": 30,
        "Create": 25,
        "description": "For capstone projects and research-based assessment"
    }
}


def show_bloom_info_cards():
    """Display informational cards for each Bloom level."""
    st.subheader("📚 Bloom's Taxonomy Levels")
    st.markdown("Learn about the six cognitive levels from foundational to creative:")
    
    cols = st.columns(3)
    
    bloom_items = list(BLOOM_LEVELS.items())
    
    for idx, (level, info) in enumerate(bloom_items):
        col = cols[idx % 3]
        with col:
            with st.container(border=True):
                st.markdown(f"### {info['icon']} {level}")
                st.markdown(f"**{info['description']}**")
                st.markdown(f"**Examples:** {', '.join(info['examples'])}")


def show_preset_distributions():
    """Allow user to select a preset Bloom distribution."""
    st.subheader("📊 Select Bloom Distribution Preset")
    
    selected_preset = st.radio(
        "Choose a distribution profile:",
        options=list(PRESET_DISTRIBUTIONS.keys()),
        index=0,
        horizontal=False
    )
    
    preset_info = PRESET_DISTRIBUTIONS[selected_preset]
    st.info(f"📌 {preset_info['description']}")
    
    return selected_preset, preset_info


def create_bloom_distribution_editor() -> Dict[str, int]:
    """
    Create interactive controls for editing Bloom distribution.
    
    Returns:
        Dict[str, int]: Bloom distribution with percentages
    """
    st.subheader("🎚️ Customize Bloom Distribution")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Adjust the percentage for each Bloom level:**")
    
    with col2:
        if st.button("📊 Load Preset", key="load_preset"):
            _, preset = show_preset_distributions()
            st.session_state.bloom_distribution = preset
    
    # Create sliders for each Bloom level
    bloom_dist = {}
    cols = st.columns(2)
    
    for idx, (level, info) in enumerate(BLOOM_LEVELS.items()):
        col = cols[idx % 2]
        
        with col:
            current_value = st.session_state.get(f"bloom_{level}", 
                                                PRESET_DISTRIBUTIONS["Balanced (Default)"][level])
            
            bloom_dist[level] = st.slider(
                f"{info['icon']} {level}",
                min_value=0,
                max_value=100,
                value=current_value,
                step=5,
                key=f"bloom_{level}"
            )
    
    # Validate and normalize
    total = sum(bloom_dist.values())
    
    # Display validation
    if total != 100:
        col_msg1, col_msg2 = st.columns([3, 1])
        with col_msg1:
            st.warning(f"⚠️ Total: {total}% (should be 100%)")
        
        with col_msg2:
            if st.button("🔄 Normalize", key="normalize_bloom"):
                # Normalize to 100%
                if total > 0:
                    bloom_dist = {k: int(v * 100 / total) for k, v in bloom_dist.items()}
                    # Fix rounding errors
                    current_total = sum(bloom_dist.values())
                    if current_total < 100:
                        bloom_dist["Apply"] += (100 - current_total)
    else:
        st.success("✅ Total: 100%")
    
    return bloom_dist


def show_bloom_distribution_visualization(bloom_dist: Dict[str, int]):
    """Visualize the Bloom distribution with a pie chart."""
    st.subheader("📈 Distribution Visualization")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create pie chart
        levels = list(bloom_dist.keys())
        percentages = list(bloom_dist.values())
        colors = [BLOOM_LEVELS[level]["color"] for level in levels]
        
        fig = go.Figure(data=[go.Pie(
            labels=levels,
            values=percentages,
            marker=dict(colors=colors),
            textposition="inside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>%{value}%<extra></extra>"
        )])
        
        fig.update_layout(
            height=400,
            showlegend=True,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Distribution Summary:**")
        
        # Categorize by complexity
        low_order = bloom_dist.get("Remember", 0) + bloom_dist.get("Understand", 0)
        middle_order = bloom_dist.get("Apply", 0)
        high_order = bloom_dist.get("Analyze", 0) + bloom_dist.get("Evaluate", 0) + bloom_dist.get("Create", 0)
        
        metric_col1, metric_col2 = st.columns(2)
        
        with metric_col1:
            st.metric("📚 Low-Order", f"{low_order}%")
            st.metric("🎯 Mid-Order", f"{middle_order}%")
        
        with metric_col2:
            st.metric("🔍 High-Order", f"{high_order}%")


def show_question_type_bloom_selector() -> Dict[str, List[str]]:
    """
    Allow users to select which Bloom levels are appropriate for each question type.
    
    Returns:
        Dict[str, List[str]]: Question type to selected Bloom levels mapping
    """
    st.subheader("🔗 Question Type → Bloom Level Mapping")
    
    st.markdown("**Configure which Bloom levels are appropriate for each question type:**")
    
    question_type_bloom = {}
    
    for qtype, default_blooms in QUESTION_TYPE_BLOOM_MAPPING.items():
        with st.expander(f"📝 {qtype}", expanded=False):
            selected_blooms = st.multiselect(
                f"Appropriate Bloom levels for {qtype}:",
                options=list(BLOOM_LEVELS.keys()),
                default=default_blooms,
                key=f"qtype_bloom_{qtype}"
            )
            
            if not selected_blooms:
                st.warning(f"⚠️ Please select at least one Bloom level for {qtype}")
                selected_blooms = default_blooms
            
            question_type_bloom[qtype] = selected_blooms
            
            # Show icon and description
            col1, col2 = st.columns([1, 4])
            with col1:
                icons = " ".join([BLOOM_LEVELS[b]["icon"] for b in selected_blooms])
                st.markdown(f"**Selected:** {icons}")
            
            with col2:
                descriptions = " → ".join([f"{BLOOM_LEVELS[b]['description']}" for b in selected_blooms])
                st.caption(descriptions)
    
    return question_type_bloom


def show_bloom_recommendations(question_types: List[str]) -> Dict[str, int]:
    """
    Show recommended Bloom distribution based on selected question types.
    
    Args:
        question_types: List of question types in the paper
        
    Returns:
        Dict[str, int]: Recommended Bloom distribution
    """
    st.subheader("💡 Recommended Bloom Distribution")
    
    st.markdown(f"Based on your selection of **{len(question_types)}** question types:")
    
    # Analyze question types to recommend distribution
    bloom_suggestions = {
        "Remember": 0,
        "Understand": 0,
        "Apply": 0,
        "Analyze": 0,
        "Evaluate": 0,
        "Create": 0
    }
    
    for qtype in question_types:
        if qtype in QUESTION_TYPE_BLOOM_MAPPING:
            blooms = QUESTION_TYPE_BLOOM_MAPPING[qtype]
            
            # Weight distribution based on question type
            weights = {
                "Multiple Choice": {"Remember": 3, "Understand": 2, "Apply": 1},
                "Short Answer": {"Understand": 1, "Apply": 2, "Analyze": 1},
                "Long Answer": {"Apply": 1, "Analyze": 2, "Evaluate": 1, "Create": 1},
                "Code Implementation": {"Apply": 2, "Analyze": 2, "Create": 1},
                "Scenario-Based": {"Apply": 1, "Analyze": 2, "Evaluate": 1},
            }
            
            type_weights = weights.get(qtype, {})
            for bloom in blooms:
                bloom_suggestions[bloom] += type_weights.get(bloom, 1)
    
    # Normalize to percentages
    total = sum(bloom_suggestions.values())
    if total > 0:
        recommended = {k: int(v * 100 / total) for k, v in bloom_suggestions.items()}
        # Fix rounding
        current_total = sum(recommended.values())
        if current_total < 100:
            recommended["Apply"] += (100 - current_total)
    else:
        recommended = PRESET_DISTRIBUTIONS["Balanced (Default)"].copy()
    
    # Remove Create key from recommended if it exists
    recommended.pop("Create", None)
    
    # Display recommendation
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        st.markdown("**Suggested Distribution:**")
        for level, percent in recommended.items():
            icon = BLOOM_LEVELS[level]["icon"]
            bar_length = int(percent / 5)
            st.markdown(f"{icon} {level}: {percent}% {'█' * bar_length}")
    
    with col_rec2:
        if st.button("✨ Apply Recommendation"):
            st.session_state.bloom_distribution = recommended
            st.success("✅ Recommendation applied!")
            st.rerun()
    
    return recommended


def show_bloom_summary_table(bloom_dist: Dict[str, int]):
    """Display a comprehensive summary table of Bloom distribution."""
    st.subheader("📋 Bloom Distribution Summary")
    
    # Create DataFrame
    data = []
    for level, percent in bloom_dist.items():
        info = BLOOM_LEVELS[level]
        data.append({
            "Level": f"{info['icon']} {level}",
            "Percentage": f"{percent}%",
            "Description": info['description'],
            "Visual": "▓" * int(percent / 5)
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Export as JSON
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("📥 Export as JSON"):
            import json
            json_str = json.dumps(bloom_dist, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="bloom_distribution.json",
                mime="application/json"
            )


# ============================================================================
# MAIN BLOOM CONFIGURATION INTERFACE
# ============================================================================

def show_bloom_configuration_wizard():
    """
    Complete interactive wizard for Bloom taxonomy configuration.
    
    Returns:
        Dict: Complete Bloom configuration
    """
    st.header("🧬 Bloom's Taxonomy Configuration Wizard")
    
    # Tabs for different configuration approaches
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 Learn",
        "🎯 Presets",
        "🎚️ Custom",
        "📊 Review"
    ])
    
    with tab1:
        st.subheader("Learn About Bloom's Taxonomy")
        show_bloom_info_cards()
        
        st.markdown("---")
        st.markdown("""
        ### Why Bloom's Taxonomy Matters?
        
        **Bloom's Taxonomy** provides a framework for understanding different levels of cognitive complexity:
        
        1. **Remember** (Foundation): Retrieving factual information
        2. **Understand** (Comprehension): Building meaning from information
        3. **Apply** (Practice): Using procedures and concepts
        4. **Analyze** (Critical): Breaking into components, relationships
        5. **Evaluate** (Judgment): Making informed decisions
        6. **Create** (Innovation): Producing new ideas/solutions
        
        A well-balanced assessment includes questions across all levels!
        """)
    
    with tab2:
        st.subheader("Quick Preset Selection")
        
        selected_preset, preset_dist = show_preset_distributions()
        
        if st.button(f"✅ Use '{selected_preset}' Preset"):
            st.session_state.bloom_distribution = preset_dist
            st.success(f"✅ '{selected_preset}' preset loaded!")
            st.rerun()
        
        st.markdown("---")
        
        # Show what each preset is good for
        st.subheader("Preset Recommendations")
        
        presets_info = {
            "Balanced (Default)": "Use when you want a mix of foundational and higher-order thinking questions",
            "Conceptual Focus": "Use for introductory courses or foundation-building assessments",
            "Application-Focused": "Use for hands-on, practical courses where doing matters more than knowing",
            "Higher-Order Thinking": "Use for advanced courses, MTech level, where critical thinking is key",
            "Research/Design Focus": "Use for capstone projects, dissertations, and research-based assessment"
        }
        
        for preset_name, recommendation in presets_info.items():
            with st.expander(f"When to use '{preset_name}'"):
                st.write(recommendation)
    
    with tab3:
        st.subheader("Custom Bloom Distribution")
        
        # Show current distribution
        if "bloom_distribution" in st.session_state:
            current_dist = st.session_state.bloom_distribution
        else:
            current_dist = PRESET_DISTRIBUTIONS["Balanced (Default)"]
        
        # Editor
        bloom_dist = create_bloom_distribution_editor()
        
        # Visualization
        show_bloom_distribution_visualization(bloom_dist)
        
        # Save button
        if st.button("💾 Save Custom Distribution"):
            st.session_state.bloom_distribution = bloom_dist
            st.success("✅ Custom distribution saved!")
    
    with tab4:
        st.subheader("Review Your Configuration")
        
        if "bloom_distribution" in st.session_state:
            bloom_dist = st.session_state.bloom_distribution
        else:
            bloom_dist = PRESET_DISTRIBUTIONS["Balanced (Default)"]
        
        show_bloom_summary_table(bloom_dist)
        
        # Statistics
        st.markdown("---")
        st.subheader("📊 Statistical Analysis")
        
        low_order = bloom_dist.get("Remember", 0) + bloom_dist.get("Understand", 0)
        middle_order = bloom_dist.get("Apply", 0)
        high_order = bloom_dist.get("Analyze", 0) + bloom_dist.get("Evaluate", 0) + bloom_dist.get("Create", 0)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📚 Low-Order Thinking", f"{low_order}%", 
                     help="Remember + Understand")
        
        with col2:
            st.metric("🎯 Application", f"{middle_order}%",
                     help="Apply level")
        
        with col3:
            st.metric("🔍 High-Order Thinking", f"{high_order}%",
                     help="Analyze + Evaluate + Create")
        
        # Assessment
        st.markdown("---")
        st.subheader("Assessment")
        
        if high_order >= 40:
            st.success("✅ Good balance of higher-order thinking!")
        elif high_order >= 20:
            st.info("ℹ️ Moderate higher-order thinking - consider increasing for advanced courses")
        else:
            st.warning("⚠️ Low higher-order thinking - consider adding more analytical questions")
    
    return st.session_state.get("bloom_distribution", PRESET_DISTRIBUTIONS["Balanced (Default)"])


# ============================================================================
# QUESTION TYPE CONFIGURATION
# ============================================================================

def show_question_type_configuration() -> List[Dict]:
    """
    Interactive interface for configuring question types in the paper.
    
    Returns:
        List[Dict]: Question type configurations
    """
    st.header("📝 Configure Question Types")
    
    # Initialize question types in session state
    if "question_configs" not in st.session_state:
        st.session_state.question_configs = [
            {
                "type": "Multiple Choice",
                "count": 10,
                "marks_each": 1,
                "difficulty": "mixed"
            }
        ]
    
    st.subheader("Paper Sections Configuration")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("**Current Question Types:**")
    
    with col3:
        if st.button("➕ Add Question Type", key="add_qtype"):
            st.session_state.question_configs.append({
                "type": "Short Answer",
                "count": 5,
                "marks_each": 4,
                "difficulty": "medium"
            })
            st.rerun()
    
    # Display and edit existing question types
    for idx, config in enumerate(st.session_state.question_configs):
        with st.expander(f"Section {idx + 1}: {config['type']}", expanded=idx == 0):
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                qtype = st.selectbox(
                    "Question Type:",
                    options=list(QUESTION_TYPE_BLOOM_MAPPING.keys()),
                    index=list(QUESTION_TYPE_BLOOM_MAPPING.keys()).index(config['type']),
                    key=f"qtype_{idx}"
                )
                config['type'] = qtype
            
            with col_b:
                count = st.number_input(
                    "Number of Questions:",
                    min_value=1,
                    max_value=50,
                    value=config['count'],
                    key=f"count_{idx}"
                )
                config['count'] = count
            
            with col_c:
                marks = st.number_input(
                    "Marks Each:",
                    min_value=1,
                    max_value=50,
                    value=config['marks_each'],
                    key=f"marks_{idx}"
                )
                config['marks_each'] = marks
            
            with col_d:
                difficulty = st.selectbox(
                    "Difficulty:",
                    options=["easy", "medium", "hard", "mixed"],
                    index=["easy", "medium", "hard", "mixed"].index(config['difficulty']),
                    key=f"diff_{idx}"
                )
                config['difficulty'] = difficulty
            
            # Show Bloom levels for this question type
            bloom_levels = QUESTION_TYPE_BLOOM_MAPPING.get(qtype, [])
            icons = " ".join([BLOOM_LEVELS[b]["icon"] for b in bloom_levels])
            st.caption(f"Bloom Levels: {icons} {', '.join(bloom_levels)}")
            
            # Delete button
            if st.button(f"🗑️ Remove {qtype}", key=f"del_{idx}"):
                st.session_state.question_configs.pop(idx)
                st.rerun()
    
    # Summary
    st.markdown("---")
    st.subheader("📊 Summary")
    
    total_questions = sum(c['count'] for c in st.session_state.question_configs)
    total_marks = sum(c['count'] * c['marks_each'] for c in st.session_state.question_configs)
    
    col_sum1, col_sum2, col_sum3 = st.columns(3)
    
    with col_sum1:
        st.metric("📝 Total Questions", total_questions)
    
    with col_sum2:
        st.metric("⭐ Total Marks", total_marks)
    
    with col_sum3:
        avg_marks = total_marks / total_questions if total_questions > 0 else 0
        st.metric("📊 Avg Marks/Q", f"{avg_marks:.1f}")
    
    return st.session_state.question_configs
