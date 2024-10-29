from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, ListView

from books.forms import BorrowBookForm
from books.models import Book, Author, Category, BookInstance, Operation, Loan


def home(request):
    books = Book.objects.all()
    borrowed_count = Loan.objects.filter(returned=False).count()
    print(f"Borrowed count: {borrowed_count}")  # Debugging line
    context = {
        'books': books,
        'borrowed_count': borrowed_count
    }

    return render(request, 'books/home2.html', context)

class BookListView(ListView):
    model = Book
    context_object_name = 'books'
    paginate_by = 4
    ordering = ['title']


class AuthorListView(ListView):
    model = Book
    context_object_name = 'books'
    paginate_by = 4
    ordering = ['title']

    def get_queryset(self):
        xx = get_object_or_404(Author, slug=self.kwargs.get('slug'))
        return Book.objects.filter(author=xx)

class CategoryListView(ListView):
    model = Book
    context_object_name = 'books'
    paginate_by = 4
    ordering = ['title']

    def get_queryset(self):
        xx = get_object_or_404(Category, slug=self.kwargs.get('slug'))
        return Book.objects.filter(category=xx)

class BookDetailView(DetailView):
    model = Book

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Zliczamy egzemplarze książki, które są dostępne (status "Dostępna")
        context['available_books_count'] = BookInstance.objects.filter(book=self.object, status='available').count()
        return context


@login_required
def borrow_book(request):
    if request.method == 'POST':
        form = BorrowBookForm(request.POST)
        if form.is_valid():
            id_code = form.cleaned_data['id_code']

            # Sprawdzamy, czy istnieje egzemplarz książki o podanym kodzie
            try:
                book_instance = BookInstance.objects.get(id_code=id_code)
            except BookInstance.DoesNotExist:
                messages.error(request, f'Nie znaleziono książki o kodzie {id_code}.')
                return redirect('borrow_book')

            # Sprawdzamy, czy książka jest dostępna do wypożyczenia
            if book_instance.status != 'available':
                messages.error(request, f'Książka "{book_instance}" nie jest dostępna do wypożyczenia.')
                return redirect('borrow_book')

            # Tworzymy wypożyczenie
            due_date = timezone.now() + timezone.timedelta(days=14)
            Loan.objects.create(
                book_instance=book_instance,
                user=request.user,
                due_date=due_date
            )

            # Zmieniamy status książki na 'borrowed'
            book_instance.status = 'borrowed'
            book_instance.save()

            messages.success(request, f'Pomyślnie wypożyczyłeś książkę: {book_instance}.')
            return redirect('borrow_book')
    else:
        form = BorrowBookForm()

    return render(request, 'books/borrow_book.html', {'form': form})


@login_required
def return_book(request):
    if request.method == 'POST':
        form = BorrowBookForm(request.POST)  # Używamy tego samego formularza do wyszukiwania książki
        if form.is_valid():
            id_code = form.cleaned_data['id_code']

            # Sprawdzamy, czy istnieje egzemplarz książki o podanym kodzie
            try:
                book_instance = BookInstance.objects.get(id_code=id_code)
            except BookInstance.DoesNotExist:
                messages.error(request, f'Nie znaleziono książki o kodzie {id_code}.')
                return redirect('return_book')

            # Sprawdzamy, czy książka jest wypożyczona przez zalogowanego użytkownika
            try:
                loan = Loan.objects.get(book_instance=book_instance, user=request.user, returned=False)
            except Loan.DoesNotExist:
                messages.error(request, f'Książka "{book_instance}" nie jest aktualnie wypożyczona przez Ciebie.')
                return redirect('return_book')

            # Aktualizujemy status wypożyczenia
            loan.returned = True
            loan.save()

            # Zmieniamy status książki na 'available'
            book_instance.status = 'available'
            book_instance.save()

            messages.success(request, f'Pomyślnie zwróciłeś książkę: {book_instance}.')
            return redirect('return_book')
    else:
        form = BorrowBookForm()

    return render(request, 'books/return_book.html', {'form': form})


@login_required
def borrowed_books_view(request):
    # Pobieramy wszystkie aktywne wypożyczenia dla zalogowanego użytkownika
    loans = Loan.objects.filter(user=request.user, returned=False)

    # Pobieramy egzemplarze książek, które są aktualnie wypożyczone
    book_instances = [loan.book_instance for loan in loans]

    return render(request, 'books/borrowed_books.html', {'book_instances': book_instances})


def book_search(request):
    query = request.GET.get('q')  # Pobierz zapytanie z formularza
    books = Book.objects.none()  # Pusty QuerySet domyślnie

    if query:
        # Wyszukiwanie książek na podstawie tytułu, opisu lub autora
        books = Book.objects.filter(
            title__icontains=query
        ) | Book.objects.filter(
            description__icontains=query
        ) | Book.objects.filter(
            author__name__icontains=query  # Użyj 'name' jako pola modelu Author
        ) | Book.objects.filter(
            author__surname__icontains=query  # Użyj 'name' jako pola modelu Author
        )

    context = {
        'books': books,
        'query': query,
    }
    return render(request, 'books/book_list.html', context)  # Możesz zmienić szablon na odpowiedni