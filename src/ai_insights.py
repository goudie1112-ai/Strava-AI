import os
from google import genai
import streamlit as st

def get_ai_coaching(weekly_summary):
    """
    Sends the weekly summary to Gemini API to get coaching insights.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ Gemini API Key not found. Please set the GEMINI_API_KEY environment variable."
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are an expert cycling and running coach. Analyze the following weekly training summary and provide 
        short, actionable insights for the athlete. Focus on training load, heart rate zones, and progression.
        Keep it concise and encouraging. Format your response in markdown.
        
        Training Summary:
        {weekly_summary}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Error generating insights: {e}"
