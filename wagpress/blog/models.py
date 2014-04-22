from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, \
    InlinePanel, PageChooserPanel
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel


class LinkFields(models.Model):
    link_external = models.URLField("External link", blank=True)
    link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        related_name='+'
    )
    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+'
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    panels = [
        FieldPanel('link_external'),
        PageChooserPanel('link_page'),
        DocumentChooserPanel('link_document'),
    ]

    class Meta:
        abstract = True


class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel('title'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


class CarouselItem(LinkFields):
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    embed_url = models.URLField("Embed URL", blank=True)
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('embed_url'),
        FieldPanel('caption'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


@python_2_unicode_compatible
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.name)

        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogEntryCarouselItem(Orderable, CarouselItem):
    entry = ParentalKey('blog.BlogEntry', related_name='carousel_items')


class BlogEntryRelatedLink(Orderable, RelatedLink):
    entry = ParentalKey('blog.BlogEntry', related_name='related_links')


class BlogEntryEmbed(Orderable):
    entry = ParentalKey('blog.BlogEntry', related_name='embeds')
    url = models.URLField()


class BlogEntry(Page):
    intro = RichTextField()
    body = RichTextField()
    created = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category)

BlogEntry.content_panels = [
    FieldPanel('title'),
    FieldPanel('intro'),
    FieldPanel('body'),
    FieldPanel('category')
]


class BlogIndexPage(Page):
    intro = RichTextField()

    def serve(self, request, **kwargs):
        posts = BlogEntry.objects.filter(live=True)
        paginate_by = getattr(settings, 'POSTS_PER_PAGE', 25)
        paginator = Paginator(posts, paginate_by)
        page = request.GET.get('page')
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        return render(request, self.template, {'posts': posts,
                                               'self': self})

BlogIndexPage.content_panels = [
    FieldPanel('title'),
    FieldPanel('intro')
]
