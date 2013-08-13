# -*- coding: utf-8 -*-
import codecs
import re
import subprocess
import markdown
from jinja2 import Markup


class PostMeta:
    def __init__(self, post_id):
        self.post_id = post_id
        self.title = post_id.replace('-', ' ')


class Tag:
    def __init__(self, tag_id, title):
        self.title = title
        self.tag_id = tag_id

    def get_url(self):
        return u'/posts/{0}'.format(self.tag_id)


class Post:
    pattern = r"\[\[([^\|]*?)\|?([^\|]*?)\]\]"  # [[title|id]] or [[id]]

    def __init__(self, post_id, working_dir=None):
        self.post_id = post_id
        self.title = post_id.replace('-', ' ')

        filename = u"{0}.md".format(post_id)
        path = u"{0}/{1}.md".format(working_dir, post_id)

        f = codecs.open(path, 'r', "utf-8")
        self.content = f.read()
        f.close()

        self.read_tags()
        self.replace_links()
        self.author, self.date = self.read_author_date(filename, working_dir)

        # markdown to html
        self.content_markup = Markup(markdown.markdown(self.content))

    def read_author_date(self, filename, working_dir):
        cmd = u"git log --diff-filter=A --date=iso -1 {0}".format(filename)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=working_dir,  shell=True)
        p.wait()

        if p.returncode == 0:
            for match in re.finditer(r"\nAuthor:[\s]*(.*?)[\s]*<[^/]*>\nDate:[\s]*(.*?)\n", p.stdout.read(), re.U):
                return match.group(1), match.group(2)
        return "", ""

    def read_tags(self):
        """
        Lorem Ipsum is simply dummy text. <- post body
        * * *                             <- horizontal rule
        [[tag1]], [[tag2 title|tag2id]]   <- tag
        """
        self.tags = []
        lines = self.content.splitlines(True)

        def is_horizontal_rule(line):
            line = "".join(line.split())
            return line.startswith(u'---') or line.startswith(u'***') or line.startswith(u'___')

        def get_raw_tags():
            raw_tags, hr = None, None
            for line in reversed(lines):
                lines.pop()
                if line.strip() == '':
                    continue

                if raw_tags is None:
                    raw_tags = line
                else:
                    return raw_tags if is_horizontal_rule(line) else None

        raw_tags = get_raw_tags()

        if raw_tags is not None:
            for match in re.finditer(Post.pattern, raw_tags, re.U):
                tag_id = match.group(2)
                title = match.group(1) if match.group(1) != '' else match.group(2)
                self.tags.append(Tag(tag_id, title))

            self.content = "".join(lines)  # content without tag lines

    def replace_links(self):
        def sub(match):
            return u"[{1}](/posts/{0})".format(match.group(2),
                                               match.group(1) if match.group(1) != '' else match.group(2))

        self.content = re.sub(Post.pattern, sub, self.content, 0, re.U)

    def get_url(self):
        return u"/posts/{0}".format(self.post_id)
