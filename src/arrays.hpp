/* -*- coding: utf-8;mode:c++;c-file-style:"stroustrup" -*- */
/*
  Licensed under the terms of the BSD 3-Clause
  (see plotpy/__init__.py for details)
*/
#ifndef __ARRAYS_HPP__
#define __ARRAYS_HPP__

#include "debug.hpp"

template <class Image>
class PixelIterator
{
public:
    typedef typename Image::value_type value_type;

    PixelIterator(Image &_img) : img(_img), cur(_img.base)
    {
    }

    value_type &operator()()
    {
        check_img_ptr("pixeliter:", cur, out, img);
        return *cur;
    }
    value_type &operator()(npy_intp dx, npy_intp dy)
    {
        return *(cur + dy * img.si + dx * img.sj);
    }
    void move(npy_intp dx, npy_intp dy)
    {
        cur += dy * img.si + dx * img.sj;
    }
    void moveto(npy_intp x, npy_intp y)
    {
        cur = img.base + y * img.si + x * img.sj;
    }

protected:
    Image &img;
    value_type *cur;
    value_type out;
};

template <class T>
class Array1D
{
public:
    typedef T value_type; // The type of pixel data from the image
    class iterator : public std::iterator<std::random_access_iterator_tag, T>
    {
    public:
        iterator() : pos(0L), stride(0) {}
        iterator(const Array1D &arr) : pos(arr.base), stride(arr.si) {}
        iterator(const iterator &it, npy_intp n = 0) : pos(it.pos), stride(it.stride) { *this += n; }
        T &operator*() { return *pos; }
        const T &operator*() const { return *pos; }
        T &operator[](npy_intp n) { return *(pos + n * stride); }
        const T &operator[](npy_intp n) const { return *(pos + n * stride); }
        iterator &operator+=(npy_intp n)
        {
            pos += stride * n;
            return *this;
        }
        npy_intp operator-(const iterator &it) { return (pos - it.pos) / stride; }
        iterator operator+(npy_intp n) { return iterator(*this, n); }
        iterator operator-(npy_intp n) { return iterator(*this, -n); }
        iterator &operator=(const iterator &it)
        {
            pos = it.pos;
            stride = it.stride;
            return *this;
        }
        iterator &operator++()
        {
            pos += stride;
            return *this;
        }
        iterator &operator--()
        {
            pos += stride;
            return *this;
        }
        iterator operator++(int)
        {
            iterator it(*this);
            pos += stride;
            return it;
        }
        iterator operator--(int)
        {
            iterator it(*this);
            pos += stride;
            return it;
        }
        bool operator<(const iterator &it) { return pos < it.pos; }
        bool operator==(const iterator &it) { return pos == it.pos; }
        bool operator!=(const iterator &it) { return pos != it.pos; }

    protected:
        T *pos;
        npy_intp stride;
    };
    Array1D() {}
    Array1D(PyArrayObject *arr)
    {
        base = (value_type *)PyArray_DATA(arr);
        ni = PyArray_DIM(arr, 0);
        si = PyArray_STRIDE(arr, 0) / sizeof(value_type);
    }

    Array1D(value_type *_base, npy_intp _ni, npy_intp _si) : base(_base), ni(_ni),
                                                             si(_si / sizeof(value_type))
    {
    }
    iterator begin() { return iterator(*this); }
    iterator end()
    {
        iterator it(*this);
        it += ni;
        return it;
    }
    void init(value_type *_base, npy_intp _ni, npy_intp _si)
    {
        base = _base;
        ni = _ni;
        si = _si;
    }

    // Pixel accessors
    value_type &value(npy_intp x)
    {
        check("array1d:", x, ni, outside);
        return *(base + x * si);
    }
    const value_type &value(npy_intp x) const
    {
        check("array1d:", x, ni, outside);
        return *(base + x * si);
    }

public:
    value_type outside;
    value_type *base;
    npy_intp ni; // dimensions
    npy_intp si; // strides in sizeof(value_type)
};

template <class T>
class Array2D
{
public:
    typedef T value_type; // The type of pixel data from the image

    Array2D() {}
    Array2D(PyArrayObject *arr)
    {
        base = (value_type *)PyArray_DATA(arr);
        ni = PyArray_DIM(arr, 0);
        nj = PyArray_DIM(arr, 1);
        si = PyArray_STRIDE(arr, 0) / sizeof(value_type);
        sj = PyArray_STRIDE(arr, 1) / sizeof(value_type);
    }

    Array2D(value_type *_base, npy_intp _ni, npy_intp _nj, npy_intp _si, npy_intp _sj) : base(_base), ni(_ni), nj(_nj),
                                                                                         si(_si / sizeof(value_type)), sj(_sj / sizeof(value_type))
    {
    }
    void init(value_type *_base, npy_intp _ni, npy_intp _nj, npy_intp _si, npy_intp _sj)
    {
        base = _base;
        ni = _ni;
        nj = _nj;
        si = _si;
        sj = _sj;
    }

    // Pixel accessors
    value_type &value(npy_intp x, npy_intp y)
    {
        check("array2d x:", x, nj, outside);
        check("array2d y:", y, ni, outside);
        return *(base + x * sj + y * si);
    }
    const value_type &value(npy_intp x, npy_intp y) const
    {
        check("array2d x:", x, nj, outside);
        check("array2d y:", y, ni, outside);
        return *(base + x * sj + y * si);
    }

public:
    value_type outside;
    value_type *base;
    npy_intp ni, nj; // dimensions
    npy_intp si, sj; // strides in sizeof(value_type)
};

template <class Image>
void set_array(Image &img, PyArrayObject *arr)
{
    img.init((typename Image::value_type *)PyArray_DATA(arr),
             PyArray_DIM(arr, 0), PyArray_DIM(arr, 1),
             PyArray_STRIDE(arr, 0) / sizeof(typename Image::value_type),
             PyArray_STRIDE(arr, 1) / sizeof(typename Image::value_type));
}

#endif
