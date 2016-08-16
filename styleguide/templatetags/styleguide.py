import os.path
from textwrap import dedent

from django import template
from django.utils.safestring import SafeString
from django.utils.html import escape
from django.utils.text import slugify


register = template.Library()


@register.tag
def guide(parser, token):
    '''
    A {% guide %} represents an HTML document composed into sections with a
    table of contents linking to them.
    '''

    nodelist = parser.parse(('endguide',))
    parser.delete_first_token()
    return GuideNode(nodelist)


class GuideNode(template.Node):

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        context['_sections'] = []

        html = self.nodelist.render(context)

        t = context.template.engine.get_template('styleguide_with_toc.html')

        result = t.render(template.Context({
            'html': html,
            'sections': context['_sections']
        }))

        del context['_sections']

        return result


@register.simple_tag
def pathname(name):
    '''
    Outputs the given project-relative path wrapped in a <code> tag.

    If the path doesn't exist, raises an exception. This is primarily
    done to prevent documentation rot.
    '''

    my_dir = os.path.abspath(os.path.dirname(__file__))
    root_dir = os.path.normpath(os.path.join(my_dir, '..', '..'))

    if not os.path.exists(os.path.join(root_dir, name)):
        raise Exception('Path %s does not exist' % name)

    return SafeString('<code>%s</code>' % escape(name))


@register.simple_tag(takes_context=True)
def guide_section(context, name):
    '''
    A section in a guide. It must be used within a {% guide %} tag.
    '''

    if '_sections' not in context:
        raise Exception(r'{% guide_section %} tags should only be used '
                        r'within {% guide%} tags!')
    section = Section(name)
    context['_sections'].append(section)
    t = context.template.engine.get_template('styleguide_section.html')

    return t.render(template.Context({'section': section}))


class Section:

    def __init__(self, name):
        self.name = name
        self.id = slugify(name)


@register.tag
def example(parser, token):
    '''
    An HTML code snippet example in a style guide. Includes both the
    rendered version of the example and the source code.
    '''

    nodelist = parser.parse(('endexample',))
    parser.delete_first_token()
    return ExampleNode(nodelist)


class ExampleNode(template.Node):

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        html = SafeString(dedent(self.nodelist.render(context)).strip())

        t = context.template.engine.get_template('styleguide_example.html')

        return t.render(template.Context({'html': html}))
