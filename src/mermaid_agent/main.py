import base64
import requests
from PIL import Image, UnidentifiedImageError
import io
from mermaid_agent.modules import llm_module
from mermaid_agent.modules import mermaid
from mermaid_agent.modules import chain

import typer
from jinja2 import Template

app = typer.Typer()


@app.command()
def test():
    print("test command")


@app.command()
def mer(
    prompt: str = typer.Option(
        ..., "--prompt", "-p", help="The prompt for generating the Mermaid chart"
    ),
    output_file: str = typer.Option(
        "mermaid.png", "--output", "-o", help="Output file name for the generated chart"
    ),
    input_file: str = typer.Option(
        None, "--input", "-i", help="Input file containing additional content"
    ),
):

    gemini_1_5_pro, gemini_1_5_flash = llm_module.build_gemini_duo()

    file_content = ""
    if input_file:
        with open(input_file, "r") as file:
            file_content = file.read()

    mermaid_prompt_1 = """You are a world-class expert at creating mermaid charts.

You follow the instructions perfectly to generate mermaid charts.

<instructions>
    <instruction>Based on the user-prompt, create the corresponding mermaid chart.</instruction>
    <instruction>Be very precise with the chart, every node and edge must be included.</instruction>
    <instruction>Use double quotes for text in the chart</instruction>
    <instruction>Respond with the mermaid chart only.</instruction>
    <instruction>Do not wrap the mermaid chart in markdown code blocks. Respond with the mermaid chart only.</instruction>
    <instruction>If you see a <file-content> section, use the content to help create the chart.</instruction>
</instructions>

[~ if file_content ~]
<file-content>
    {{file_content}}
</file-content>
[~ endif ~]

<examples>
    <example>
        <user-chart-request>
            Create a flowchart that shows A flowing to E. At C, branch out to H and I.
        </user-chart-request>
        <chart-response>
            graph LR;
                A
                B
                C
                D
                E
                H
                I

                A --> B
                A --> C
                A --> D
                C --> H
                C --> I
                D --> E
        </chart-response>
    </example>
    <example>
        <user-chart-request>
            Build a pie chart that shows the distribution of Apples: 40, Bananas: 35, Oranges: 25.
        </user-chart-request>
        <chart-response>
            pie title Distribution of Fruits
                "Apples" : 40
                "Bananas" : 35
                "Oranges" : 25
        </chart-response>
    </example>
    <example>
        <user-chart-request>
            State diagram for a traffic light. Still, Moving, Crash.
        </user-chart-request>
        <chart-response>
            stateDiagram-v2
                [*] --> Still
                Still --> [*]

                Still --> Moving
                Moving --> Still
                Moving --> Crash
                Crash --> [*]
        </chart-response>
    </example>
    <example>
        <user-chart-request>
            Create a timeline of major social media platforms from 2002 to 2006.
        </user-chart-request>
        <chart-response>
            timeline
                title History of Social Media Platforms
                2002 : LinkedIn
                2004 : Facebook
                     : Google
                2005 : Youtube
                2006 : Twitter
        </chart-response>
    </example>
</examples>

<user-prompt>
    {{ user_prompt }}
</user-prompt>

Your mermaid chart:"""

    mermaid_prompt_2 = """You are a world-class expert at creating mermaid charts.

Your co-worker has just generated a mermaid chart.

It's your job to review the chart to ensure it's correct.

If you see any mistakes, be very precise in what the mistakes are.

<instructions>
    <instruction>Review the chart to ensure it's correct.</instruction>
    <instruction>Be very precise in your critique.</instruction>
    <instruction>If you see any mistakes, correct them.</instruction>
    <instruction>Respond with the corrected mermaid chart.</instruction>
    <instruction>Do not wrap the mermaid chart in markdown code blocks. Respond with the mermaid chart only.</instruction>
    <instruction>If the chart is already correct, respond with the chart only.</instruction>
</instructions>

<mermaid-chart>
    {{output[-1]}}
</mermaid-chart>

Your critique of the mermaid chart:"""

    context = {"user_prompt": prompt, "file_content": file_content}
    conditional_context = {"file_content": file_content}

    # Render the template with the context
    rendered_mermaid_prompt_1 = Template(
        mermaid_prompt_1, block_start_string="[~", block_end_string="~]"
    ).render(conditional_context)

    prompt_response, ctx_filled_prompts = chain.MinimalChainable.run(
        context,
        gemini_1_5_pro,
        llm_module.prompt,
        prompts=[rendered_mermaid_prompt_1, mermaid_prompt_2],
    )

    chain.MinimalChainable.to_delim_text_file(
        "mermaid_prompt_1_results", prompt_response
    )

    chain.MinimalChainable.to_delim_text_file(
        "mermaid_prompt_1_ctx_filled_prompts", ctx_filled_prompts
    )

    res = llm_module.parse_markdown_backticks(prompt_response[-1])

    print(res)

    mermaid.mm(res, output_file)


def main():
    app()
